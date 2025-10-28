"""
Python-to-Dafny Translator - Converts Python code to Dafny for verification.
"""
import ast
from typing import Optional, Dict, List
from ..models.specifications import FormalSpecification


class PythonToDafnyTranslator:
    """Translates Python code to Dafny code."""

    def __init__(self):
        """Initialize the translator."""
        self.indent_level = 0
        self.indent_size = 4

    def translate(self, python_code: str, spec: FormalSpecification) -> str:
        """
        Translate Python code to Dafny.

        Args:
            python_code: Python function code as a string.
            spec: Formal specification with contracts.

        Returns:
            Dafny code as a string.

        Raises:
            ValueError: If translation fails.
        """
        try:
            tree = ast.parse(python_code)

            # Find the function definition
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_def = node
                    break

            if not func_def:
                raise ValueError("No function definition found in Python code")

            # Generate Dafny code
            dafny_code = self._translate_function(func_def, spec)

            return dafny_code

        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
        except Exception as e:
            raise ValueError(f"Translation failed: {e}")

    def _translate_function(self, node: ast.FunctionDef, spec: FormalSpecification) -> str:
        """Translate a Python function to a Dafny method."""
        # Method signature
        method_name = self._to_pascal_case(node.name)
        params = self._translate_parameters(node.args, spec)
        return_type = self._translate_type(spec.return_type)

        lines = []
        lines.append(f"method {method_name}({params}) returns (result: {return_type})")

        # Add preconditions
        for precond in spec.preconditions:
            dafny_precond = self._translate_condition(precond, spec)
            lines.append(f"    requires {dafny_precond}")

        # Add postconditions
        for postcond in spec.postconditions:
            dafny_postcond = self._translate_condition(postcond, spec)
            lines.append(f"    ensures {dafny_postcond}")

        # Method body
        lines.append("{")

        # Translate statements
        body_lines = self._translate_statements(node.body, spec, indent=1)
        lines.extend(body_lines)

        lines.append("}")

        return "\n".join(lines)

    def _translate_parameters(self, args: ast.arguments, spec: FormalSpecification) -> str:
        """Translate function parameters to Dafny."""
        params = []
        for i, arg in enumerate(args.args):
            param_name = arg.arg
            # Find type from spec
            param_type = "int"  # default
            for p in spec.parameters:
                if p.name == param_name:
                    param_type = self._translate_type(p.type)
                    break

            params.append(f"{param_name}: {param_type}")

        return ", ".join(params)

    def _translate_type(self, python_type: str) -> str:
        """Translate Python type to Dafny type."""
        # Handle common type mappings
        type_map = {
            "int": "int",
            "bool": "bool",
            "str": "string",
            "float": "real",
        }

        # Handle list types
        if python_type.startswith("list["):
            inner_type = python_type[5:-1]
            dafny_inner = self._translate_type(inner_type)
            return f"seq<{dafny_inner}>"

        # Handle Optional types
        if python_type.startswith("Optional["):
            inner_type = python_type[9:-1]
            dafny_inner = self._translate_type(inner_type)
            return f"{dafny_inner}"  # Dafny doesn't have Optional, use nullable

        return type_map.get(python_type, "int")

    def _translate_condition(self, condition: str, spec: FormalSpecification) -> str:
        """Translate a natural language condition to Dafny logic."""
        # This is a simplified translation - in practice, this would need
        # more sophisticated NLP or pattern matching

        condition_lower = condition.lower()

        # Handle common patterns
        if "not empty" in condition_lower or "non-empty" in condition_lower:
            for param in spec.parameters:
                if param.name in condition_lower:
                    return f"|{param.name}| > 0"

        if "sorted" in condition_lower:
            for param in spec.parameters:
                if param.name in condition_lower and "list[" in param.type:
                    return f"forall i, j :: 0 <= i < j < |{param.name}| ==> {param.name}[i] <= {param.name}[j]"

        # Handle result conditions
        if "result" in condition_lower:
            if ">= 0" in condition_lower:
                # Extract array indexing pattern
                if "[result]" in condition_lower:
                    for param in spec.parameters:
                        if f"{param.name}[result]" in condition_lower:
                            parts = condition_lower.split("==")
                            if len(parts) == 2:
                                target = parts[1].strip()
                                return f"result >= 0 ==> 0 <= result < |{param.name}| && {param.name}[result] == {target}"

                return "result >= 0 ==> " + condition

        # Default: try to convert directly (may need refinement)
        # Replace common Python operators with Dafny equivalents
        dafny_cond = condition
        dafny_cond = dafny_cond.replace(" and ", " && ")
        dafny_cond = dafny_cond.replace(" or ", " || ")
        dafny_cond = dafny_cond.replace(" not ", " ! ")
        dafny_cond = dafny_cond.replace("len(", "|")
        dafny_cond = dafny_cond.replace(")", "|")

        return dafny_cond

    def _translate_statements(self, stmts: List[ast.stmt], spec: FormalSpecification, indent: int = 0) -> List[str]:
        """Translate a list of Python statements to Dafny."""
        lines = []
        indent_str = "    " * indent

        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                lines.extend(self._translate_assign(stmt, indent_str))
            elif isinstance(stmt, ast.AugAssign):
                lines.extend(self._translate_aug_assign(stmt, indent_str))
            elif isinstance(stmt, ast.Return):
                lines.extend(self._translate_return(stmt, indent_str))
            elif isinstance(stmt, ast.If):
                lines.extend(self._translate_if(stmt, spec, indent))
            elif isinstance(stmt, ast.While):
                lines.extend(self._translate_while(stmt, spec, indent))
            elif isinstance(stmt, ast.For):
                lines.extend(self._translate_for(stmt, spec, indent))
            elif isinstance(stmt, ast.Expr):
                # Skip standalone expressions
                pass

        return lines

    def _translate_assign(self, node: ast.Assign, indent_str: str) -> List[str]:
        """Translate assignment statement."""
        if len(node.targets) != 1:
            raise ValueError("Multiple assignment targets not supported")

        target = self._translate_expr(node.targets[0])
        value = self._translate_expr(node.value)

        return [f"{indent_str}var {target} := {value};"]

    def _translate_aug_assign(self, node: ast.AugAssign, indent_str: str) -> List[str]:
        """Translate augmented assignment (+=, -=, etc.)."""
        target = self._translate_expr(node.target)
        value = self._translate_expr(node.value)
        op = self._translate_operator(node.op)

        return [f"{indent_str}{target} := {target} {op} {value};"]

    def _translate_return(self, node: ast.Return, indent_str: str) -> List[str]:
        """Translate return statement."""
        if node.value:
            value = self._translate_expr(node.value)
            return [f"{indent_str}return {value};"]
        else:
            return [f"{indent_str}return;"]

    def _translate_if(self, node: ast.If, spec: FormalSpecification, indent: int) -> List[str]:
        """Translate if statement."""
        lines = []
        indent_str = "    " * indent

        condition = self._translate_expr(node.test)
        lines.append(f"{indent_str}if {condition} {{")

        # Translate body
        body_lines = self._translate_statements(node.body, spec, indent + 1)
        lines.extend(body_lines)

        # Handle else/elif
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # elif case
                lines.append(f"{indent_str}}} else if {self._translate_expr(node.orelse[0].test)} {{")
                body_lines = self._translate_statements(node.orelse[0].body, spec, indent + 1)
                lines.extend(body_lines)
            else:
                # else case
                lines.append(f"{indent_str}}} else {{")
                else_lines = self._translate_statements(node.orelse, spec, indent + 1)
                lines.extend(else_lines)

        lines.append(f"{indent_str}}}")

        return lines

    def _translate_while(self, node: ast.While, spec: FormalSpecification, indent: int) -> List[str]:
        """Translate while loop."""
        lines = []
        indent_str = "    " * indent

        condition = self._translate_expr(node.test)
        lines.append(f"{indent_str}while {condition}")

        # Add loop invariants
        for invariant in spec.loop_invariants:
            dafny_inv = self._translate_condition(invariant, spec)
            lines.append(f"{indent_str}    invariant {dafny_inv}")

        lines.append(f"{indent_str}{{")

        # Translate body
        body_lines = self._translate_statements(node.body, spec, indent + 1)
        lines.extend(body_lines)

        lines.append(f"{indent_str}}}")

        return lines

    def _translate_for(self, node: ast.For, spec: FormalSpecification, indent: int) -> List[str]:
        """Translate for loop to while loop in Dafny."""
        lines = []
        indent_str = "    " * indent

        # For loops need to be converted to while loops in Dafny
        # This is a simplified version
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            # Handle range() loops
            target = self._translate_expr(node.target)
            if len(node.iter.args) == 1:
                # range(n)
                start = "0"
                end = self._translate_expr(node.iter.args[0])
            elif len(node.iter.args) == 2:
                # range(start, end)
                start = self._translate_expr(node.iter.args[0])
                end = self._translate_expr(node.iter.args[1])
            else:
                raise ValueError("range() with step not supported")

            lines.append(f"{indent_str}var {target} := {start};")
            lines.append(f"{indent_str}while {target} < {end}")

            # Add loop invariants
            for invariant in spec.loop_invariants:
                dafny_inv = self._translate_condition(invariant, spec)
                lines.append(f"{indent_str}    invariant {dafny_inv}")

            lines.append(f"{indent_str}{{")

            # Translate body
            body_lines = self._translate_statements(node.body, spec, indent + 1)
            lines.extend(body_lines)

            # Increment counter
            lines.append(f"{indent_str}    {target} := {target} + 1;")

            lines.append(f"{indent_str}}}")

        return lines

    def _translate_expr(self, node: ast.expr) -> str:
        """Translate an expression."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "true" if node.value else "false"
            return str(node.value)
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            return str(node.n)
        elif isinstance(node, ast.BinOp):
            left = self._translate_expr(node.left)
            right = self._translate_expr(node.right)
            op = self._translate_operator(node.op)
            return f"({left} {op} {right})"
        elif isinstance(node, ast.UnaryOp):
            operand = self._translate_expr(node.operand)
            op = self._translate_unary_operator(node.op)
            return f"{op}{operand}"
        elif isinstance(node, ast.Compare):
            left = self._translate_expr(node.left)
            ops = [self._translate_comparison(op) for op in node.ops]
            comparators = [self._translate_expr(c) for c in node.comparators]

            # Build comparison chain
            result = left
            for op, comp in zip(ops, comparators):
                result = f"{result} {op} {comp}"
            return result
        elif isinstance(node, ast.Subscript):
            value = self._translate_expr(node.value)
            index = self._translate_expr(node.slice)
            return f"{value}[{index}]"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "len":
                arg = self._translate_expr(node.args[0])
                return f"|{arg}|"
            # Handle other function calls
            func = self._translate_expr(node.func)
            args = [self._translate_expr(arg) for arg in node.args]
            return f"{func}({', '.join(args)})"
        elif isinstance(node, ast.List):
            elements = [self._translate_expr(e) for e in node.elts]
            return f"[{', '.join(elements)}]"
        elif isinstance(node, ast.BoolOp):
            op = " && " if isinstance(node.op, ast.And) else " || "
            values = [self._translate_expr(v) for v in node.values]
            return f"({op.join(values)})"
        else:
            # Fallback for unsupported expressions
            return "0"  # placeholder

    def _translate_operator(self, op: ast.operator) -> str:
        """Translate binary operator."""
        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "/",
            ast.Mod: "%",
        }
        return op_map.get(type(op), "+")

    def _translate_unary_operator(self, op: ast.unaryop) -> str:
        """Translate unary operator."""
        op_map = {
            ast.UAdd: "+",
            ast.USub: "-",
            ast.Not: "!",
        }
        return op_map.get(type(op), "")

    def _translate_comparison(self, op: ast.cmpop) -> str:
        """Translate comparison operator."""
        op_map = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
        }
        return op_map.get(type(op), "==")

    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)

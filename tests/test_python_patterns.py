"""Tests for Python pattern definitions and analysis logic."""

import ast
import tempfile
from pathlib import Path

import pytest

from claudex_guard.standards.python_patterns import PythonPatterns


class TestPythonPatterns:
  """Test Python pattern definitions and analysis methods."""
  
  def setup_method(self):
    """Set up test fixtures."""
    self.patterns = PythonPatterns()
  
  def test_banned_imports_definitions(self):
    """Test that banned imports are properly defined."""
    banned = self.patterns.get_banned_imports()
    
    assert "requests" in banned
    assert "httpx" in banned["requests"]
    assert "pip" in banned
    assert "uv" in banned["pip"]
    assert "os.path" in banned
    assert "pathlib" in banned["os.path"]
  
  def test_required_patterns_definitions(self):
    """Test that required patterns are properly defined."""
    required = self.patterns.get_required_patterns()
    
    assert "f_strings" in required
    assert "pathlib_usage" in required
    assert "type_hints" in required
    assert "context_managers" in required
  
  def test_antipatterns_definitions(self):
    """Test that antipatterns are properly defined."""
    antipatterns = self.patterns.get_antipatterns()
    
    assert len(antipatterns) > 0
    assert all(isinstance(pattern, tuple) and len(pattern) == 2 for pattern in antipatterns)
    
    # Check for key antipatterns
    pattern_messages = [msg for _, msg in antipatterns]
    assert any("Mutable default argument" in msg for msg in pattern_messages)
    assert any("Bare except clause" in msg for msg in pattern_messages)
    assert any("f-strings" in msg for msg in pattern_messages)
  
  def test_analyze_ast_missing_type_hints(self):
    """Test AST analysis detects missing type hints."""
    code = """
def function_without_type_hint():
    return "test"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      tree = ast.parse(code)
      violations = self.patterns.analyze_ast(tree, file_path)
      
      assert len(violations) == 1
      assert violations[0].violation_type == "missing_type_hints"
      assert "function_without_type_hint" in violations[0].message
      assert violations[0].function_name == "function_without_type_hint"
      assert violations[0].ast_node is not None
    finally:
      file_path.unlink()
  
  def test_analyze_ast_mutable_default_argument(self):
    """Test AST analysis detects mutable default arguments."""
    code = """
def bad_function(items=[]):
    return items

def another_bad_function(config={}):
    return config
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      tree = ast.parse(code)
      violations = self.patterns.analyze_ast(tree, file_path)
      
      mutable_violations = [v for v in violations if v.violation_type == "mutable_default"]
      assert len(mutable_violations) == 2
      
      function_names = {v.function_name for v in mutable_violations}
      assert "bad_function" in function_names
      assert "another_bad_function" in function_names
    finally:
      file_path.unlink()
  
  def test_analyze_ast_banned_imports(self):
    """Test AST analysis detects banned imports."""
    code = """
import requests
from os.path import join
import pip
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      tree = ast.parse(code)
      violations = self.patterns.analyze_ast(tree, file_path)
      
      banned_violations = [v for v in violations if v.violation_type == "banned_import"]
      assert len(banned_violations) >= 2  # requests and pip at minimum
      
      import_names = {v.language_context["import_name"] for v in banned_violations}
      assert "requests" in import_names
      assert "pip" in import_names
    finally:
      file_path.unlink()
  
  def test_analyze_patterns_antipatterns(self):
    """Test pattern analysis detects antipatterns."""
    code_lines = [
      "def bad_function(items=[]):",
      "    try:",
      "        result = 'Hello %s' % name",
      "    except:",
      "        pass",
      "    return items"
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write('\n'.join(code_lines))
      f.flush()
      file_path = Path(f.name)
    
    try:
      violations = self.patterns.analyze_patterns(code_lines, file_path)
      
      assert len(violations) >= 2  # At least mutable default and bare except
      violation_types = {v.language_context["pattern"] for v in violations}
      
      # Check for key antipatterns
      mutable_default_found = any(r"def\s+\w+\([^)]*=\s*\[\]" in pattern for pattern in violation_types)
      bare_except_found = any(r"except\s*:" in pattern for pattern in violation_types)
      
      assert mutable_default_found
      assert bare_except_found
    finally:
      file_path.unlink()
  
  def test_analyze_imports_missing_pathlib(self):
    """Test import analysis detects missing pathlib."""
    code = """
def process_files():
    with open('test.txt', 'r') as f:
        content = f.read()
    return content
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      violations = self.patterns.analyze_imports(code, file_path)
      
      pathlib_violations = [v for v in violations if v.violation_type == "missing_pathlib"]
      assert len(pathlib_violations) == 1
      assert "pathlib" in pathlib_violations[0].language_context["missing_import"]
    finally:
      file_path.unlink()
  
  def test_analyze_imports_old_formatting(self):
    """Test import analysis detects old string formatting."""
    code = """
name = "World"
message = "Hello %s" % name
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      violations = self.patterns.analyze_imports(code, file_path)
      
      formatting_violations = [v for v in violations if v.violation_type == "old_formatting"]
      assert len(formatting_violations) == 1
      assert "old_percent" in formatting_violations[0].language_context["formatting_style"]
    finally:
      file_path.unlink()
  
  def test_analyze_development_patterns_exception_without_logging(self):
    """Test development pattern analysis detects exception handling without logging."""
    code = """
def process_data():
    try:
        result = risky_operation()
        return result
    except Exception as e:
        return None
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      lines = code.splitlines()
      violations = self.patterns.analyze_development_patterns(code, lines, file_path)
      
      logging_violations = [v for v in violations if v.violation_type == "error_handling"]
      assert len(logging_violations) == 1
      assert "exception_without_logging" in logging_violations[0].language_context["pattern"]
    finally:
      file_path.unlink()
  
  def test_analyze_development_patterns_heavy_inheritance(self):
    """Test development pattern analysis detects heavy inheritance usage."""
    code = """
class Base:
    pass

class Child1(Base):
    def __init__(self):
        super().__init__()

class Child2(Base):
    def __init__(self):
        super().__init__()
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      lines = code.splitlines()
      violations = self.patterns.analyze_development_patterns(code, lines, file_path)
      
      composition_violations = [v for v in violations if v.violation_type == "composition_violation"]
      assert len(composition_violations) == 1
      assert composition_violations[0].language_context["class_count"] > 0
      assert composition_violations[0].language_context["inheritance_count"] > 0
    finally:
      file_path.unlink()
  
  def test_all_analysis_methods_return_violations_list(self):
    """Test that all analysis methods return lists of Violation objects."""
    code = "def test(): pass"
    lines = ["def test(): pass"]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(code)
      f.flush()
      file_path = Path(f.name)
    
    try:
      tree = ast.parse(code)
      
      ast_violations = self.patterns.analyze_ast(tree, file_path)
      pattern_violations = self.patterns.analyze_patterns(lines, file_path)
      import_violations = self.patterns.analyze_imports(code, file_path)
      dev_violations = self.patterns.analyze_development_patterns(code, lines, file_path)
      
      assert isinstance(ast_violations, list)
      assert isinstance(pattern_violations, list)
      assert isinstance(import_violations, list)
      assert isinstance(dev_violations, list)
    finally:
      file_path.unlink()
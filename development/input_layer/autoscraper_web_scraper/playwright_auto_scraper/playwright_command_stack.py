from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List, OrderedDict
from collections import OrderedDict
import json
from pathlib import Path
import ast
from datetime import datetime

from typing import Any, AsyncIterable, Iterable


async def async_exec(code: str) -> Any:
    """
    Make an async function with the code and `exec` it
    """
    exec(
        f'async def __ex(): ' +
        ''.join(f'\n {l}' for l in code.split('\n'))
    )

    # Get `__ex` from local variables, call it and return the result
    return await locals()['__ex']()


@dataclass
class PlaywrightRule:
    _rule_sequence: list[tuple[dict,...]] #list['PlaywrightCommandBase']


    def __post_init__(self):
        self._rule_sequence = [
            tuple(command for command in rule)
            for rule in self._rule_sequence
        ]


    @property
    def rule_sequence(self) -> list[tuple[str,...]]: #list['PlaywrightCommandBase']:
        return self._rule_sequence


    @rule_sequence.setter
    def rule_sequence(self, value: tuple|list[tuple]) -> list[tuple[str,...]]: #list['PlaywrightCommandBase']:
        if isinstance(value, tuple):
            self._rule_sequence.append(value)
        elif isinstance(value, (AsyncIterable, Iterable)):
            -_ = [self._rule_sequence.append(val) for val in value if isinstance(val, tuple)]
        else:
            raise ValueError(f'Invalid value type {type(value)}. accepting only list or tuple')




@dataclass
class PlaywrightCommandBase:
    """Base dataclass for all Playwright commands"""
    command_type: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    selector: Optional[str] = None
    description: Optional[str] = None

@dataclass
class ClickCommand(PlaywrightCommandBase):
    """Click action command"""
    position: Optional[tuple[float, float]] = None
    button: str = "left"
    click_count: int = 1
    delay: Optional[float] = None
    force: bool = False
    modifiers: Optional[List[str]] = None
    timeout: Optional[float] = None

@dataclass
class TypeCommand(PlaywrightCommandBase):
    """Keyboard input command"""
    text: str
    delay: Optional[float] = None
    timeout: Optional[float] = None
    no_wait_after: bool = False

@dataclass
class NavigateCommand(PlaywrightCommandBase):
    """Page navigation command"""
    url: str
    wait_until: str = "load"  # One of: load, domcontentloaded, networkidle, commit
    timeout: Optional[float] = None
    referer: Optional[str] = None

@dataclass
class WaitForSelectorCommand(PlaywrightCommandBase):
    """Wait for element command"""
    state: str = "visible"  # One of: attached, detached, visible, hidden
    timeout: Optional[float] = None
    strict: bool = False

@dataclass
class FillCommand(PlaywrightCommandBase):
    """Form fill command"""
    value: str
    force: bool = False
    timeout: Optional[float] = None
    no_wait_after: bool = False

@dataclass
class SelectCommand(PlaywrightCommandBase):
    """Dropdown select command"""
    values: List[str]
    timeout: Optional[float] = None
    no_wait_after: bool = False

class PlaywrightCommandStack:
    """
    Manages an ordered collection of Playwright commands.
    Can be created from recorded demos or Playwright Python sequences.
    """
    def __init__(self):
        self.commands: OrderedDict[int, PlaywrightCommandBase] = OrderedDict()
        self._command_counter = 0

    def add_command(self, command: PlaywrightCommandBase) -> None:
        """Add a command to the stack"""
        self.commands[self._command_counter] = command
        self._command_counter += 1

    def get_commands(self) -> List[PlaywrightCommandBase]:
        """Get all commands in order"""
        return list(self.commands.values())

    def clear(self) -> None:
        """Clear all commands from the stack"""
        self.commands.clear()
        self._command_counter = 0

    @classmethod
    def from_recording(cls, recording_path: Union[str, Path]) -> 'PlaywrightCommandStack':
        """
        Create a PlaywrightCommandStack from a recorded demo file (JSON format)
        """
        stack = cls()
        recording_path = Path(recording_path)

        with open(recording_path, 'r') as f:
            recorded_actions = json.load(f)

        command_mapping = {
            'click': ClickCommand,
            'type': TypeCommand,
            'navigate': NavigateCommand,
            'waitForSelector': WaitForSelectorCommand,
            'fill': FillCommand,
            'select': SelectCommand
        }

        for action in recorded_actions:
            command_type = action.get('type')
            command_class = command_mapping.get(command_type)

            if command_class:
                # Remove type from action dict as it's already captured in command_type
                action_data = action.copy()
                action_data.pop('type', None)
                
                # Convert position from dict to tuple if present
                if 'position' in action_data:
                    pos = action_data['position']
                    action_data['position'] = (pos.get('x'), pos.get('y'))

                command = command_class(command_type=command_type, **action_data)
                stack.add_command(command)

        return stack

    @classmethod
    def from_python_sequence(cls, sequence_path: Union[str, Path]) -> 'PlaywrightCommandStack':
        """
        Create a PlaywrightCommandStack from a Python file containing Playwright commands
        """
        stack = cls()
        sequence_path = Path(sequence_path)

        with open(sequence_path, 'r') as f:
            code = f.read()

        tree = ast.parse(code)
        
        def extract_kwargs(node: ast.Call) -> dict:
            kwargs = {}
            for keyword in node.keywords:
                if isinstance(keyword.value, ast.Constant):
                    kwargs[keyword.arg] = keyword.value.value
                elif isinstance(keyword.value, ast.List):
                    kwargs[keyword.arg] = [
                        elem.value for elem in keyword.value.elts
                        if isinstance(elem, ast.Constant)
                    ]
            return kwargs

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'attr'):
                    method_name = node.func.attr
                    kwargs = extract_kwargs(node)

                    # Map Playwright method names to command types
                    command = None
                    if method_name == 'click':
                        command = ClickCommand(command_type='click', **kwargs)
                    elif method_name == 'type':
                        command = TypeCommand(command_type='type', **kwargs)
                    elif method_name in ('goto', 'navigate'):
                        command = NavigateCommand(command_type='navigate', **kwargs)
                    elif method_name == 'wait_for_selector':
                        command = WaitForSelectorCommand(command_type='waitForSelector', **kwargs)
                    elif method_name == 'fill':
                        command = FillCommand(command_type='fill', **kwargs)
                    elif method_name == 'select_option':
                        command = SelectCommand(command_type='select', **kwargs)

                    if command:
                        stack.add_command(command)

        return stack

    def to_json(self, output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
        """
        Convert the command stack to JSON format
        If output_path is provided, saves to file; otherwise returns JSON string
        """
        commands_dict = [
            {
                'type': cmd.command_type,
                'timestamp': cmd.timestamp,
                'selector': cmd.selector,
                'description': cmd.description,
                **{k: v for k, v in cmd.__dict__.items() 
                   if k not in ['command_type', 'timestamp', 'selector', 'description']}
            }
            for cmd in self.commands.values()
        ]

        json_str = json.dumps(commands_dict, indent=2)
        
        if output_path:
            output_path = Path(output_path)
            output_path.write_text(json_str)
            return None
            
        return json_str

    def to_python_code(self, output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
        """
        Convert the command stack to executable Python code
        If output_path is provided, saves to file; otherwise returns code string
        """
        code_lines = [
            "from playwright.sync_api import sync_playwright",
            "",
            "def run(playwright):",
            "    browser = playwright.chromium.launch()",
            "    context = browser.new_context()",
            "    page = context.new_page()",
            ""
        ]

        for cmd in self.commands.values():
            if isinstance(cmd, NavigateCommand):
                code_lines.append(f"    page.goto('{cmd.url}', "
                                f"wait_until='{cmd.wait_until}'"
                                f"{f', timeout={cmd.timeout}' if cmd.timeout else ''})")
            
            elif isinstance(cmd, ClickCommand):
                code_lines.append(f"    page.click('{cmd.selector}'"
                                f"{f', position={cmd.position}' if cmd.position else ''}"
                                f"{f', button=\'{cmd.button}\'' if cmd.button != 'left' else ''}"
                                f"{f', delay={cmd.delay}' if cmd.delay else ''})")
            
            elif isinstance(cmd, TypeCommand):
                code_lines.append(f"    page.type('{cmd.selector}', '{cmd.text}'"
                                f"{f', delay={cmd.delay}' if cmd.delay else ''})")
            
            elif isinstance(cmd, WaitForSelectorCommand):
                code_lines.append(f"    page.wait_for_selector('{cmd.selector}', "
                                f"state='{cmd.state}'"
                                f"{f', timeout={cmd.timeout}' if cmd.timeout else ''})")
            
            elif isinstance(cmd, FillCommand):
                code_lines.append(f"    page.fill('{cmd.selector}', '{cmd.value}'"
                                f"{f', force={cmd.force}' if cmd.force else ''})")
            
            elif isinstance(cmd, SelectCommand):
                values_str = "[" + ", ".join(f"'{v}'" for v in cmd.values) + "]"
                code_lines.append(f"    page.select_option('{cmd.selector}', {values_str})")

        code_lines.extend([
            "",
            "    # Cleanup",
            "    context.close()",
            "    browser.close()",
            "",
            "with sync_playwright() as playwright:",
            "    run(playwright)"
        ])

        code_str = "\n".join(code_lines)
        
        if output_path:
            output_path = Path(output_path)
            output_path.write_text(code_str)
            return None
            
        return code_str

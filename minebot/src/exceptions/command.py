class CommandExecutionError(Exception):
    def __str__(self) -> str:
        return self.args[0] if self.args else "Command execution failed"

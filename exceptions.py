from discord.ext.commands import CommandError, CheckFailure


class PathDoesNotExist(CommandError):
    def __init__(self, e):
        self.original = e
        super().__init__('Path does not exist: {0.__class__.__name__}: {0}'.format(e))


class NotInChannel(CheckFailure):
    pass

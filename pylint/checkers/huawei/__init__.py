# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from pylint.utils import register_plugins


def register(linter):
    """Required method to auto register this checker."""
    register_plugins(linter, __path__[0])

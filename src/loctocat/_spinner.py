"""
Houses the :class:`_Spinner` class. This module is considered internal and should not be imported outside of the
library.
"""

from __future__ import annotations

from typing import Union

from halo import Halo


class _Spinner:
    """
    A wrapper around :class:`halo.Halo`. This class is considered internal and should not be imported outside of the
    library.
    """
    def __init__(self, spinner: Union[Halo, None]):
        self.spinner = spinner

    @staticmethod
    def spin_condition(func):
        def wrapper(spinner, *args, **kwargs):
            if spinner.spinner:
                return func(spinner, *args, **kwargs)
            else:
                return spinner

        return wrapper

    @spin_condition
    def __enter__(self):
        return self.spinner.start()

    @spin_condition
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.spinner.stop()

    @spin_condition
    def succeed(self):
        self.spinner.succeed()

    @spin_condition
    def fail(self):
        self.spinner.fail()

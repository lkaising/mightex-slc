"""Reserved contract constants."""

from __future__ import annotations


REPEAT_FOREVER: int = 9999
"""Strobe repeat count value that repeats the profile indefinitely.

Because this value is reserved, a strobe profile cannot be asked to output
exactly 10000 times. Pass REPEAT_FOREVER for indefinite repetition instead.
"""

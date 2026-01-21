# Intentionally buggy code for testing observers
#
# This file contains multiple issues that observers should catch:
# 1. Syntax issues (but valid enough to parse)
# 2. Logic errors
# 3. Security vulnerabilities
# 4. Missing error handling
# 5. Type inconsistencies


def process_user_data(user_input):
    """Process user data - MULTIPLE ISSUES HERE."""
    # BUG: SQL injection vulnerability
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"

    # BUG: No input validation
    # BUG: Using eval on user input (code injection)
    result = eval(user_input)

    # BUG: Hardcoded credentials
    password = "admin123"
    api_key = "sk-1234567890abcdef"

    return result


def calculate_average(numbers):
    """Calculate average - has division by zero risk."""
    # BUG: No check for empty list (division by zero)
    total = sum(numbers)
    return total / len(numbers)


def read_config(filename):
    """Read config file - missing error handling."""
    # BUG: No error handling for file not found
    # BUG: File handle never closed (no context manager)
    f = open(filename)
    data = f.read()
    return data


def parse_json_unsafe(json_string):
    """Parse JSON - but doesn't actually use json module."""
    import json

    # BUG: Catches all exceptions silently
    try:
        return json.loads(json_string)
    except:
        pass


class UserManager:
    """User management with issues."""

    def __init__(self):
        # BUG: Mutable default-like pattern
        self.users = []
        self._cache = {}

    def add_user(self, name, email):
        # BUG: No validation of email format
        # BUG: Duplicate users allowed
        self.users.append({"name": name, "email": email})

    def find_user(self, name):
        # BUG: Linear search, inefficient for large lists
        # BUG: Returns None implicitly if not found (should raise or be explicit)
        for user in self.users:
            if user["name"] == name:
                return user

    def delete_all_users(self):
        # BUG: Dangerous operation with no confirmation
        # BUG: No audit logging
        self.users = []


# BUG: Global mutable state
GLOBAL_COUNTER = [0]


def increment_counter():
    """Increment global counter - thread unsafe."""
    # BUG: Not thread-safe
    GLOBAL_COUNTER[0] += 1
    return GLOBAL_COUNTER[0]


# BUG: Unused import would be caught by linter
import sys
import os
import subprocess

# BUG: Wildcard import
from typing import *

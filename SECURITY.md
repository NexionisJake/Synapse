# Security Implementation for Synapse AI Web Application

This document describes the comprehensive security measures implemented in the Synapse AI web application to protect against various security threats and ensure safe operation.

## Overview

The security implementation includes:
- Input validation and sanitization
- File system access restrictions
- Resource limits and rate limiting
- Error message sanitization
- Content filtering for dangerous patterns

## Security Components

### 1. Input Validation (`security.py`)

#### Message Content Validation
- **Maximum length**: 10,000 characters per message
- **HTML escaping**: All user input is HTML-escaped to prevent XSS
- **Dangerous pattern detection**: Blocks script tags, JavaScript URLs, event handlers, and system calls
- **Empty content prevention**: Rejects empty or whitespace-only messages

#### Conversation History Validation
- **Maximum conversation length**: 200 messages
- **Role validation**: Only allows 'user', 'assistant', and 'system' roles
- **Structure validation**: Ensures proper message format with required fields
- **Content sanitization**: Each message is individually validated and sanitized

#### System Prompt Validation
- **Maximum length**: 5,000 characters
- **Content filtering**: Same dangerous pattern detection as messages
- **HTML escaping**: Prevents injection attacks through prompts

### 2. File System Security

#### Path Restrictions
- **Project directory confinement**: All file operations restricted to project directory
- **Absolute path blocking**: Prevents access to system directories like `/etc`, `/usr`, `/home`
- **Path traversal prevention**: Resolves and validates all paths to prevent `../` attacks

#### File Extension Filtering
- **Allowed extensions**: `.json`, `.txt`, `.log`, `.md`
- **Blocked extensions**: Executable files (`.exe`, `.sh`, `.bat`) and other potentially dangerous formats

#### File Size Limits
- **Maximum file size**: 10MB per file
- **JSON payload limit**: 1MB maximum for API requests

### 3. Content Filtering

#### Dangerous Pattern Detection
The system blocks content containing:
- Script tags: `<script>`, `</script>`
- JavaScript URLs: `javascript:`
- Event handlers: `onclick`, `onload`, etc.
- Code execution: `eval()`, `exec()`, `__import__`
- System calls: `subprocess`, `system()`
- OS imports: `import os`

#### Sensitive Information Patterns
Error messages are sanitized to remove:
- Passwords and API keys
- File paths (replaced with `[PATH]`)
- Tokens and secrets (replaced with `[REDACTED]`)
- Stack traces (replaced with generic messages)

### 4. Resource Limits

#### Conversation Limits
- **Maximum messages**: 200 per conversation
- **Maximum message length**: 10,000 characters
- **Automatic cleanup**: Old messages removed when limits exceeded

#### File Limits
- **Memory file size**: Monitored and limited
- **Disk space checking**: Ensures sufficient space before file operations
- **Backup creation**: Automatic backups before file modifications

### 5. Error Handling Security

#### Error Message Sanitization
- **Path removal**: File paths replaced with generic `[PATH]` placeholder
- **Credential removal**: Passwords, keys, and tokens replaced with `[REDACTED]`
- **Stack trace hiding**: Internal errors show generic messages to users
- **Context-aware messages**: Different error types get appropriate user-friendly messages

#### Error Categories
- **Permission errors**: "Access denied. Please check permissions."
- **File not found**: "Required file not found."
- **Connection errors**: "Service connection failed. Please try again."
- **Internal errors**: "An internal error occurred. Please try again."

## Implementation Details

### Security Decorator

The `@security_required` decorator is applied to all API endpoints:

```python
@app.route('/chat', methods=['POST'])
@security_required(validate_json=True, validate_conversation=True)
def chat():
    # Endpoint implementation
```

### File Access Validation

All file operations go through security validation:

```python
# Before any file operation
is_allowed, error_msg = validate_file_access(file_path, "read")
if not is_allowed:
    raise SecurityError(error_msg)
```

### Input Sanitization

All user inputs are validated and sanitized:

```python
is_valid, sanitized_content = InputValidator.validate_message_content(user_input)
if not is_valid:
    return error_response(sanitized_content)
```

## Security Configuration

### Configurable Limits

All security limits are defined in `SecurityConfig`:

```python
class SecurityConfig:
    MAX_MESSAGE_LENGTH = 10000
    MAX_CONVERSATION_LENGTH = 200
    MAX_PROMPT_LENGTH = 5000
    MAX_JSON_SIZE = 1024 * 1024  # 1MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
```

### Allowed File Extensions

```python
ALLOWED_EXTENSIONS = {'.json', '.txt', '.log', '.md'}
```

### Restricted Paths

```python
RESTRICTED_PATHS = {
    '/etc', '/usr', '/bin', '/sbin', '/root', '/home',
    'C:\\Windows', 'C:\\Program Files', 'C:\\Users'
}
```

## Security Testing

### Automated Tests

The security implementation includes comprehensive tests:

1. **Input validation tests**: Test all validation functions with valid and invalid inputs
2. **File system security tests**: Test path restrictions and file access controls
3. **Error sanitization tests**: Verify sensitive information is properly removed
4. **Integration tests**: Test security measures in the full Flask application

### Test Coverage

- ✅ Valid input acceptance
- ✅ Dangerous content blocking
- ✅ File path restrictions
- ✅ Resource limit enforcement
- ✅ Error message sanitization
- ✅ JSON payload validation
- ✅ Conversation length limits

## Security Best Practices

### For Developers

1. **Always use security decorators** on new API endpoints
2. **Validate all user inputs** before processing
3. **Use file access validation** for any file operations
4. **Sanitize error messages** before returning to users
5. **Test security measures** for all new features

### For Deployment

1. **Run security tests** before deployment
2. **Monitor error logs** for security violations
3. **Keep security limits** appropriate for your environment
4. **Regular security audits** of file permissions and access

## Monitoring and Logging

### Security Events Logged

- Input validation failures
- File access violations
- Resource limit exceeded
- Dangerous content detection
- Error message sanitization

### Log Format

```
[TIMESTAMP] - [LEVEL] - [ERROR_ID] security: [MESSAGE]
```

### Error Statistics

The system tracks:
- Total security violations
- Violations by category
- Recent security events
- Error patterns and trends

## Future Enhancements

### Planned Security Features

1. **Rate limiting**: Prevent abuse through request rate limiting
2. **IP-based restrictions**: Block suspicious IP addresses
3. **Content analysis**: Advanced AI-based content filtering
4. **Audit logging**: Comprehensive security audit trails
5. **Encryption**: Encrypt sensitive data at rest

### Security Monitoring

1. **Real-time alerts**: Immediate notification of security events
2. **Dashboard**: Security metrics and violation tracking
3. **Automated responses**: Automatic blocking of repeated violations
4. **Forensic analysis**: Detailed investigation tools

## Compliance

This security implementation helps ensure compliance with:

- **Data Protection**: User data is protected and not exposed in errors
- **Access Control**: Strict file system access controls
- **Input Validation**: All inputs are validated and sanitized
- **Error Handling**: Secure error handling prevents information disclosure

## Contact

For security-related questions or to report security issues, please review the code and test the security measures thoroughly before deployment.
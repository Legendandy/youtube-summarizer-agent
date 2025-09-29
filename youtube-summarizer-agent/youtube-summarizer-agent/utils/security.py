import re
from typing import List, Tuple, Optional


class SecurityValidator:
    """Validates user input for security threats"""
    
    # SQL Injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|DECLARE)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(;.*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b)",
        r"(\bxp_\w+)",
        r"(\bsp_\w+)",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"(&&|\|\||;|\||`)",
        r"(\$\(.*\))",
        r"(\bwget\b|\bcurl\b|\bchmod\b|\bchown\b)",
        r"(\brm\b.*-rf)",
        r"(\bmkdir\b|\btouch\b|\bcat\b.*\/etc)",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\.\/|\.\.\\)",
        r"(\/etc\/passwd|\/etc\/shadow)",
        r"(\\windows\\system32)",
    ]
    
    # Script injection patterns
    SCRIPT_INJECTION_PATTERNS = [
        r"(<script[^>]*>.*?<\/script>)",
        r"(javascript:)",
        r"(onerror\s*=)",
        r"(onload\s*=)",
        r"(eval\s*\()",
        r"(<iframe[^>]*>)",
    ]
    
    # Excessive length or repetition (DoS attempts)
    MAX_PROMPT_LENGTH = 5000
    MAX_URL_LENGTH = 2048
    MAX_REPEATED_CHARS = 50
    
    def __init__(self):
        """Initialize security validator"""
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.cmd_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMMAND_INJECTION_PATTERNS]
        self.path_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self.script_patterns = [re.compile(p, re.IGNORECASE) for p in self.SCRIPT_INJECTION_PATTERNS]
    
    def _check_patterns(self, text: str, patterns: List[re.Pattern], threat_type: str) -> Tuple[bool, Optional[str]]:
        """
        Checks text against a list of patterns
        
        Args:
            text: Text to check
            patterns: List of compiled regex patterns
            threat_type: Type of threat for error message
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        for pattern in patterns:
            if pattern.search(text):
                return False, f"Potential {threat_type} detected"
        return True, None
    
    def _check_length(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if text length is within acceptable limits
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if len(text) > self.MAX_PROMPT_LENGTH:
            return False, f"Input exceeds maximum length of {self.MAX_PROMPT_LENGTH} characters"
        return True, None
    
    def _check_repeated_chars(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Checks for excessive character repetition (potential DoS)
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        # Check for any character repeated more than MAX_REPEATED_CHARS times
        pattern = re.compile(r'(.)\1{' + str(self.MAX_REPEATED_CHARS) + ',}')
        if pattern.search(text):
            return False, "Excessive character repetition detected"
        return True, None
    
    def _check_url_length(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if URLs in text are within acceptable length
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        # Find all URLs in text
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(text)
        
        for url in urls:
            if len(url) > self.MAX_URL_LENGTH:
                return False, f"URL exceeds maximum length of {self.MAX_URL_LENGTH} characters"
        
        return True, None
    
    def _check_null_bytes(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Checks for null bytes (potential exploit)
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if '\x00' in text:
            return False, "Null bytes detected in input"
        return True, None
    
    def validate(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Performs comprehensive security validation on input text
        
        Args:
            text: User input text to validate
            
        Returns:
            Tuple of (is_safe, error_message)
            - is_safe: True if input passes all checks, False otherwise
            - error_message: Description of security issue if unsafe, None if safe
        """
        if not text or not isinstance(text, str):
            return False, "Invalid input: text must be a non-empty string"
        
        # Check length
        is_safe, error = self._check_length(text)
        if not is_safe:
            return False, error
        
        # Check URL length
        is_safe, error = self._check_url_length(text)
        if not is_safe:
            return False, error
        
        # Check repeated characters
        is_safe, error = self._check_repeated_chars(text)
        if not is_safe:
            return False, error
        
        # Check null bytes
        is_safe, error = self._check_null_bytes(text)
        if not is_safe:
            return False, error
        
        # Check SQL injection
        is_safe, error = self._check_patterns(text, self.sql_patterns, "SQL injection")
        if not is_safe:
            return False, error
        
        # Check command injection
        is_safe, error = self._check_patterns(text, self.cmd_patterns, "command injection")
        if not is_safe:
            return False, error
        
        # Check path traversal
        is_safe, error = self._check_patterns(text, self.path_patterns, "path traversal")
        if not is_safe:
            return False, error
        
        # Check script injection
        is_safe, error = self._check_patterns(text, self.script_patterns, "script injection")
        if not is_safe:
            return False, error
        
        return True, None
    
    def sanitize_for_log(self, text: str, max_length: int = 100) -> str:
        """
        Sanitizes text for safe logging
        
        Args:
            text: Text to sanitize
            max_length: Maximum length of sanitized output
            
        Returns:
            Sanitized text safe for logging
        """
        # Remove any control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized
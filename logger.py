# color codes for better logging output
class Colors:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def log_info(message: str, color: str = Colors.CYAN):
    """Logs an informational message with a specified color."""
    print(f"{color}ℹ️ {message}{Colors.END}")


def log_success(message: str):
    """Logs a success message with a specified color."""
    print(f"{Colors.GREEN}✅{message}{Colors.END}")


def log_error(message: str):
    """Logs an error message with a specified color."""
    print(f"{Colors.RED}❌{message}{Colors.END}")


def log_warning(message: str):
    """Logs a warning message with a specified color."""
    print(f"{Colors.YELLOW}⚠️{message}{Colors.END}")


def log_header(message: str):
    """Logs a header message with a emphasis."""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.PURPLE}🚀{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.PURPLE}{'='*60}{Colors.END}\n")

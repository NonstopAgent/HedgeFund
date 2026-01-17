"""
Octane Global Trust - Visual Branding Module
Obsidian/Chrome aesthetic for console output
"""

from colorama import init, Fore, Style
from datetime import datetime

# Initialize colorama for Windows support
init(autoreset=True)

# Octane color palette (Obsidian/Chrome)
OBSIDIAN = Fore.WHITE + Style.DIM
CHROME = Fore.WHITE + Style.BRIGHT
ACCENT = Fore.CYAN
WARNING = Fore.YELLOW
SUCCESS = Fore.GREEN
ERROR = Fore.RED


def print_header():
    """Print the Octane Global Trust header"""
    print("\n" + "=" * 80)
    print(f"{CHROME}{'OCTANE GLOBAL TRUST':^80}{Style.RESET_ALL}")
    print(f"{OBSIDIAN}{'Predator Investment Engine':^80}{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def print_section(title: str):
    """Print a section header"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{CHROME}{'─' * 80}{Style.RESET_ALL}")
    print(f"{CHROME}{title:<60}{OBSIDIAN}{timestamp:>20}{Style.RESET_ALL}")
    print(f"{CHROME}{'─' * 80}{Style.RESET_ALL}\n")


def print_agent_status(agent_name: str, status: str, details: str = ""):
    """Print agent status with branding"""
    status_colors = {
        "ACTIVE": ACCENT,
        "COMPLETE": SUCCESS,
        "ERROR": ERROR,
        "STANDBY": OBSIDIAN
    }
    color = status_colors.get(status, CHROME)
    
    print(f"{color}[{status:8}]{Style.RESET_ALL} {CHROME}{agent_name:<20}{Style.RESET_ALL}", end="")
    if details:
        print(f" {OBSIDIAN}{details}{Style.RESET_ALL}")
    else:
        print()


def print_ticker_card(ticker: str, confidence: float, summary: str):
    """Print a formatted ticker card"""
    print(f"\n{CHROME}{'─' * 80}{Style.RESET_ALL}")
    print(f"{CHROME}  TICKER:{Style.RESET_ALL} {ACCENT}{ticker:<10}{Style.RESET_ALL}", end="")
    print(f"{CHROME}CONFIDENCE:{Style.RESET_ALL} {SUCCESS if confidence >= 8.0 else WARNING}{confidence:.1f}/10.0{Style.RESET_ALL}")
    print(f"{OBSIDIAN}  {summary[:76]}...{Style.RESET_ALL}")
    print(f"{CHROME}{'─' * 80}{Style.RESET_ALL}\n")


def print_footer():
    """Print the footer"""
    print(f"\n{CHROME}{'─' * 80}{Style.RESET_ALL}")
    print(f"{OBSIDIAN}{'Ghost Mode Ready — Running Silent':^80}{Style.RESET_ALL}")
    print(f"{CHROME}{'─' * 80}{Style.RESET_ALL}\n")

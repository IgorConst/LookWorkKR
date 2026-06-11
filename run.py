import sys
from pathlib import Path

# Гарантируем, что корень проекта находится в путях поиска Python
# Это нужно, чтобы работали импорты вида "from lwk.main import main"
sys.path.insert(0, str(Path(__file__).parent))

from lwk.main import main

if __name__ == "__main__":
    main()
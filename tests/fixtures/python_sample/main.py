"""Sample main entry point."""

from utils import helper_function
from models import User


def main():
    user = User("Alice")
    result = helper_function(user.name)
    print(result)


if __name__ == "__main__":
    main()

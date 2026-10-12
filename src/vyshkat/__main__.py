from vyshkat.container import Container


def main() -> None:
    try:
        Container().console().run()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()

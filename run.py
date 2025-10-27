"""Entry point for running the DementiaReasoningApp demo server."""

from dementia_reasoning_app import DementiaReasoningApp


def main() -> None:
    app = DementiaReasoningApp(__name__)
    app.run()


if __name__ == "__main__":
    main()

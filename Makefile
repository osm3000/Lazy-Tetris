generate_requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

run_game:
	poetry run python LazyBlocks.py
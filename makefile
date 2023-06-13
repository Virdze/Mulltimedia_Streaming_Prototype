.DEFAULT_GOAL			:= clean

.PHONY: clean
clean:
	@rm -f src/*.pyc
	@rm -rf src/__pycache__
	@rm -f cache-0.jpg

JS_DIR ?= library/static
TS ?=  $(shell find $(JS_DIR) -name "*.ts")

all: javascript
javascript: $(TS)
	tsc
clean:
	-git clean -f -X $(JS_DIR)

MPY_CROSS ?= mpy-cross
MPREMOTE ?= mpremote
BUILD_DIR := build
PORT ?= auto

PY_FILES := $(shell find . -path ./$(BUILD_DIR) -prune -o -type f -name "*.py" ! -path "./main.py" -print)
MPY_FILES := $(patsubst ./%, $(BUILD_DIR)/%, $(PY_FILES:.py=.mpy))
OTHER_FILES := $(shell find . -path ./$(BUILD_DIR) -prune -o \( -type f ! -name "*.py" ! -name "*.mpy" -o -path "./main.py" \) -print)
COPY_FILES := $(patsubst ./%, $(BUILD_DIR)/%, $(OTHER_FILES))

.PHONY: all clean upload run clean-badge compile

all: $(MPY_FILES) $(COPY_FILES)

$(BUILD_DIR)/%.mpy: %.py
	@echo "Compiling $<"
	@mkdir -p $(dir $@)
	@$(MPY_CROSS) -march=armv6m $< -o $@
	@touch $@

$(BUILD_DIR)/%: %
	@echo "Copying $< -> $@"
	@mkdir -p $(dir $@)
	@cp $< $@

clean:
	@echo "Cleaning build directory and .pyc files..."
	@rm -rf $(BUILD_DIR)
	@find . -path ./$(BUILD_DIR) -prune -o -name "*.pyc" -exec rm {} \;

clean-badge:
	@echo "Removing all files from badge..."
	$(MPREMOTE) connect $(PORT) fs rm -r :/

compile: all
	@echo "Compilation complete. Files are ready in $(BUILD_DIR)."

upload: compile
	cd $(BUILD_DIR) && $(MPREMOTE) connect $(PORT) cp -r . :/ && cd ..

run: upload
	$(MPREMOTE) connect $(PORT) run main.py

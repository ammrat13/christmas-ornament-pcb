MPY_CROSS := ./mpy-cross
MPY_FLAGS := -v -O2

# List all the files that need to be compiled. This does not include `code.py`,
# since CircuitPython does not recognize `.mpy` files as the main script.
PY_FILES := \
	platform.py \
	config.py \
	ble.py \
	driver/bluefruitspi.py \
	task/__init__.py \
	task/heap_monitor.py \
	task/battery_monitor.py \
	task/led.py \
	task/neopixel.py \
	task/util.py
MPY_FILES := $(PY_FILES:.py=.mpy)

.PHONY: all
all: $(MPY_FILES)

.PHONY: clean
clean:
	rm -f $(MPY_FILES)

.PHONY: install
install: code.py $(MPY_FILES)
ifndef PREFIX
	$(error PREFIX is not set)
endif
	install -t $(PREFIX) code.py
	for mpy_file in $(MPY_FILES); do \
		targ=$(PREFIX)/$$(dirname $$mpy_file); \
		install -d $$targ; \
		install -t $$targ $$mpy_file; \
	done
	sync

%.mpy: %.py
	$(MPY_CROSS) $(MPY_FLAGS) $<

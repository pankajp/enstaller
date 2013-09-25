default: foo_x86 foo_amd64

foo_x86: src/empty_main.c
	$(CC) $< -o $@ -arch i386

foo_amd64: src/empty_main.c
	$(CC) $< -o $@ -arch x86_64

clean:
	rm -f foo_x86
	rm -f foo_amd64

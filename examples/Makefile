.PHONY: all

all: .fw/shim_upload.toml .fw/shim_upload.py

# Upload TOML to all Flywheel Prisma projects
.fw/shim_upload.toml: shim-emails.toml | .fw/
	@echo "Uploading $< to Flywheel PRISMA projects..."
	@for dest in fw://mrrc/Prisma1QA fw://mrrc/Prisma2QA fw://mrrc/Prisma3QA; do \
		fw upload "$<" "$$dest"; \
	done
	@date > $@
# Upload Python script to all Flywheel PRISMA projects
.fw/shim_upload.py: shim_notify.py | .fw/
	@echo "Uploading $< to Flywheel PRISMA projects..."
	@for dest in fw://mrrc/Prisma1QA fw://mrrc/Prisma2QA fw://mrrc/Prisma3QA; do \
		fw upload "$<" "$$dest"; \
	done
	@date > $@

# Ensure .fw/ directory exists
%/:
	mkdir -p $@

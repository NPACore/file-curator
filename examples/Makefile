.SUFFIXES:
.PHONY: all shim launch bids test

all: test shim launch bids

shim: .fw/qa/shim_upload.py .fw/qa/shim_settings.toml
launch: .fw/launchqa # launch_qc.py
bids: .fw/bids/complete_test.joblog  # complete_test.py
test: .test.log

upload_prereq_QA = for dest in fw://mrrc/Prisma{1,2,3}QA; do fw upload $< $$dest; done
# string as make macro: run upload across all QA destinations (shell for loop)
# hard codes first make recipete prerequisit ("$<") as file to upload
# this replaces repleated loop
#  @echo "Uploading $< to Flywheel PRISMA projects..."
#  @for dest in fw://mrrc/Prisma1QA fw://mrrc/Prisma2QA fw://mrrc/Prisma3QA; do \
#  	fw upload "$<" "$$dest"; \
#  done

## all tests (2025-09-08: only tests for shim)
.test.log: $(wildcard *.py tests/*.py)
	test -r ../.venv && source ../.venv/bin/activate && \
	python3 -m pytest tests/ | tee $@

## z-shim threshold test gear
# Upload config TOML to all Flywheel Prisma projects
.fw/qa/shim_settings.toml: shim_settings.toml | .fw/qa/
	$(upload_prereq_QA)
	@date > $@

# Upload Python script to all Flywheel PRISMA projects
.fw/qa/shim_upload.py: shim_notify.py | .fw/qa/
	$(upload_prereq_QA)
	@date > $@

## BIDS completion test gear -- test if BIDS is complete
.fw/bids/complete_test.upload: complete_test.py | .fw/bids/
	fw upload $< fw://flywheel/bids/
	date > $@

.fw/bids/complete_test.gear: .fw/bids/complete_test.upload
	../mrrc/file-curator_project_bids.py > $@
	date >> $@

.fw/bids/complete_test.joblog: .fw/bids/complete_test.gear
   JOBID=$(shell sed -n s/jobid = //p' $< ) && \
	fw job wait $(JOBID) && \
	  python -c 'import flywheel;fw=flywheel.Client(); j=fw.jobs.find_one("_id=$(JOBID)").print_logs()' > $@


## Launch QA -- run new comp-intensive tSNR QA job with HPC tag 
.fw/launchqa: .fw/launchqa.code .fw/launchqa.key
	date > $@
.fw/launchqa.code: ../examples/launch_qc.py | .fw/
	$(upload_prereq_QA)
	date > $@
.fw/launchqa.key: ../examples/npac_api.fernet | .fw/
	$(upload_prereq_QA)
	date > $@

# Ensure .fw/ and .fw/qa directory exists
%/:
	mkdir -p $@

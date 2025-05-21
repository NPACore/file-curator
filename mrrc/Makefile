.PHONY: all

all: .fw/complete_test.gear

.fw/z-shim.upload: ../examples/shim_notify.py
	fw upload $< fw://mrrc/Prisma1QA/
	#fw upload ../examples/shim-emails.toml fw://mrrc/Prisma1QA/
	#fw downlaod fw://mrrc/Prisma1QA/files/shim-emails.toml
	date > $@

.fw/complete_test.upload: ../examples/complete_test.py | .fw/
	fw upload $< fw://flywheel/bids/
	date > $@

.fw/complete_test.gear: .fw/complete_test.upload
	./file-curator_project_bids.py > $@
	date >> $@

.fw/complete_test.joblog: .fw/complete_test.gear
   JOBID=$(shell sed -n s/jobid = //p' $< ) && \
	fw job wait $(JOBID) && \
	  python -c 'import flywheel;fw=flywheel.Client(); j=fw.jobs.find_one("_id=$(JOBID)").print_logs()' > $@

%/:
	mkdir -p $@

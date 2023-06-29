#!/bin/bash

# Set the maximum number of concurrent jobs across distributed network
n_jobs=8

BASE_JOB_URL=https://job-server.com

# Run forever
while true; do
    # Wait for a free slot
    while [ "$(jobs -r | wc -l)" -ge "${n_jobs}" ]; do
        sleep 5
    done

    # Get the next job
    sleep 30
    echo "========================="
    echo "Requesting for new job..."
    job=$(curl -sS "${BASE_JOB_URL}/get-job")

    # Check if there are no more jobs
    if [ -z "${job}" ]; then
        break
    fi

    # Extract the input_file property from the job
    input_file=$(echo "${job}" | jq -r '.input_file')
    input_file_basename=$(basename "${input_file}")
    job_db_id=$(echo "${job}" | jq -r '.id')

    echo "Preparing job id ${job_db_id} for ${input_file}"

    # Spawn a new process to run the command
    (
        set -x;
        job_id=$(bacalhau docker run --id-only --wait --network=full -i "https://data.commoncrawl.org/${input_file}" symato/cc:v0.2.8 -- python /app/main_bacalhau.py --input_file "${input_file_basename}" --dump "CC-MAIN-2023-14" --repo_id "Symato/cc")

        # Wait for the process to finish and get the job id
        sleep 15

        wait "${job_id}"

        # Get the job status
        status_payload=$(bacalhau describe "${job_id}" --json | jq)

        # Report the job status back to the server
        curl -X POST -H "Content-Type: application/json" -d "${status_payload}" "${BASE_JOB_URL}/report-job?id=${job_db_id}"
        set +x;
    ) &
done

# Wait for all jobs to finish
wait

CREATE TABLE experiments (
    exp_id SERIAL PRIMARY KEY,
    start_time VARCHAR,
    end_time VARCHAR
                         );

CREATE TABLE deployments (
    exp_id INT,
    deployment_uid VARCHAR,
    -- when the deployment became known to the api server
    creation_time VARCHAR,
    PRIMARY KEY(deployment_uid),
    CONSTRAINT fk_deployment FOREIGN KEY(exp_id) REFERENCES experiments(exp_id)
                         );

CREATE TABLE pods (
    exp_id INT,
    deployment_uid VARCHAR,
    pod_name VARCHAR,
    -- when the pod was created - id est was scheduled to a node - can be null if pod was never assigned
    start_time VARCHAR,
    -- can be null if pod was never assigned
    assigned_node VARCHAR,
    -- how long it took to assign the pod in microseconds - can be null if pod was never assigned
    scheduling_duration VARCHAR,
    latency_request INT,
    tcp_mbpns_request INT,
    udp_mbpns_request INT,
    jitter_request INT,
    CONSTRAINT fk_pods1 FOREIGN KEY(exp_id) REFERENCES experiments(exp_id),
    CONSTRAINT fk_pods2 FOREIGN KEY(deployment_uid) REFERENCES deployments(deployment_uid)
    CONSTRAINT pod_key PRIMARY KEY (exp_id, pod_name)
);

CREATE TYPE metric_type AS ENUM('LAT', 'TCP', 'UDP', 'JIT');

CREATE TYPE result_type AS ENUM('success', 'fail', 'error');

CREATE TABLE scheduling_results (
    exp_id INT,
--     cannot be accessed from scheduler logs :(
--     deployment_uid VARCHAR,
    pod_name VARCHAR,
    node VARCHAR,
    metric metric_type NOT NULL,
    metric_value FLOAT,
    -- shows if the node was considered a fit in the filtering step of the scheduling process for this metric - doesn't mean this node was chosen
    result result_type NOT NULL,
    -- when the metric value was measured
    measuring_time VARCHAR,
    -- when the scheduling decision was made
    scheduling_time VARCHAR,
    CONSTRAINT fk_scheduling1 FOREIGN KEY(exp_id) REFERENCES experiments(exp_id),
--     CONSTRAINT fk_scheduling2 FOREIGN KEY(deployment_uid) REFERENCES deployments(deployment_uid),
    CONSTRAINT fk_scheduling3 FOREIGN KEY(pod_name) REFERENCES pods(pod_name),
    CONSTRAINT scheduling_key PRIMARY KEY (exp_id, pod_name, node, metric)
);


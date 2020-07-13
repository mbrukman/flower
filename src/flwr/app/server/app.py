# Copyright 2020 Adap GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Flower server app."""


from logging import INFO
from typing import Dict

from flwr.grpc_server.grpc_server import start_insecure_grpc_server
from flwr.logger import log
from flwr.server import Server


def start_server(server_address: str, server: Server, config: Dict[str, int]) -> None:
    """Start a Flower server using the gRPC transport layer."""
    grpc_server = start_insecure_grpc_server(
        client_manager=server.client_manager(), server_address=server_address
    )
    log(INFO, "Flower server running (insecure, %s rounds)", config["num_rounds"])

    # Fit model
    hist = server.fit(num_rounds=config["num_rounds"])
    log(INFO, "app_fit: losses_distributed %s", str(hist.losses_distributed))
    log(INFO, "app_fit: accuracies_distributed %s", str(hist.accuracies_distributed))
    log(INFO, "app_fit: losses_centralized %s", str(hist.losses_centralized))
    log(INFO, "app_fit: accuracies_centralized %s", str(hist.accuracies_centralized))

    # Temporary workaround to force distributed evaluation
    server.strategy.eval_fn = None  # type: ignore

    # Evaluate the final trained model
    res = server.evaluate(rnd=-1)
    if res is not None:
        loss, (results, failures) = res
        log(INFO, "app_evaluate: federated loss: %s", str(loss))
        log(
            INFO,
            "app_evaluate: results %s",
            str([(res[0].cid, res[1]) for res in results]),
        )
        log(INFO, "app_evaluate: failures %s", str(failures))
    else:
        log(INFO, "app_evaluate: no evaluation result")

    # Stop the gRPC server
    grpc_server.stop(1)
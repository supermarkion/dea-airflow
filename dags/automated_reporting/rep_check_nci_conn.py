# -*- coding: utf-8 -*-

"""
check nci conn dat
"""
from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime

class MySSHOperator(SSHOperator):

    def execute(self, context=None) -> Union[bytes, str]:
        result: Union[bytes, str]
        if self.command is None:
            raise AirflowException("SSH operator error: SSH command not specified. Aborting.")

        # Forcing get_pty to True if the command begins with "sudo".
        self.get_pty = self.command.startswith('sudo') or self.get_pty

        try:
            with self.get_ssh_client() as ssh_client:
                result = self.run_ssh_client_command(ssh_client, self.command)
        except Exception as e:
            raise AirflowException(f"SSH operator error: {str(e)}")
        return result.decode('utf-8')

default_args = {
    "owner": "Ramkumar Ramagopalan",
    "start_date": datetime(2020, 3, 12),
    "retries": 0,
    "timeout": 1200,  # For running SSH Commands
    "email_on_failure": True,
    "email": "ramkumar.ramagopalan@ga.gov.au",
}

dag = DAG(
    "test_nci_conn_dev",
    default_args=default_args,
    schedule_interval=None,
    tags=["dev"],
)

with dag:
    print_ga_storage_task = MySSHOperator(
        task_id="print_storage_file",
        ssh_conn_id="lpgs_gadi",
        command="cat /scratch/v10/usage_reports/ga_storage_usage_latest.csv",
        do_xcom_push=True,
    )
    print_ga_storage_task

import datetime as dtime
from unittest.mock import Mock, patch

from api.models import Agency, Events, Launch, Program
from api.models.launcher_config import LauncherConfig
from api.models.rocket import Rocket
from configurations.models import LaunchStatus, ProgramType
from django.test import TestCase
from django.utils import timezone

from autoscaler.autoscaler import check_autoscaler
from autoscaler.digitalocean_helper import DigitalOceanHelper
from autoscaler.models import AutoscalerSettings


class AutoscalerTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create required launch status records
        LaunchStatus.objects.create(id=1, full_name="Go", abbrev="Go")
        LaunchStatus.objects.create(id=2, full_name="TBD", abbrev="TBD")
        LaunchStatus.objects.create(id=3, full_name="Success", abbrev="Success")
        LaunchStatus.objects.create(id=4, full_name="Failure", abbrev="Failure")

        # Create test launch service providers
        self.spacex = Agency.objects.create(name="SpaceX", info_url="https://spacex.com")
        self.ula = Agency.objects.create(name="United Launch Alliance", info_url="https://ula.com")
        self.rocket_lab = Agency.objects.create(name="Rocket Lab", info_url="https://rocketlab.com")
        self.other_provider = Agency.objects.create(name="Other Space Company", info_url="https://other.com")

        # Create test programs with program type
        program_type = ProgramType.objects.create(id=1, name="Development Program")
        self.starship_program = Program.objects.create(
            name="Starship Development", description="SpaceX Starship development program", program_type=program_type
        )
        self.other_program = Program.objects.create(
            name="Other Program", description="Some other program", program_type=program_type
        )

        # Create autoscaler settings
        self.autoscaler_settings = AutoscalerSettings.objects.create(
            enabled=True,
            max_workers=10,
            current_workers=2,
            spacex_weight=3,
            ula_weight=2,
            rocket_lab_weight=2,
            other_weight=1,
            starship_launch_weight=5,
            starship_event_weight=3,
            custom_worker_count=None,
        )

        # Create launcher config and rocket for launches
        self.launcher_config = LauncherConfig.objects.create(name="Test Rocket", manufacturer=self.spacex)

    def create_test_launch(self, name, launch_time, launch_service_provider, programs=None):
        """Helper method to create a test launch with required rocket"""
        rocket = Rocket.objects.create(configuration=self.launcher_config)
        launch = Launch.objects.create(
            name=name, net=launch_time, launch_service_provider=launch_service_provider, rocket=rocket
        )
        if programs:
            for program in programs:
                launch.program.add(program)
        return launch

    def test_autoscaler_disabled(self):
        """Test autoscaler when disabled"""
        self.autoscaler_settings.enabled = False
        self.autoscaler_settings.save()

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should not call update methods when disabled
            mock_do_instance.update_node_pools.assert_not_called()
            mock_do_instance.update_keda_min_replicas.assert_not_called()

    def test_spacex_launch_scaling(self):
        """Test scaling for SpaceX launches"""
        # Create SpaceX launch within 1 hour window
        launch_time = timezone.now() + dtime.timedelta(minutes=30)
        self.create_test_launch("Falcon 9 Test", launch_time, self.spacex)

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should scale to 1 (base) + 3 (SpaceX weight) = 4 workers
            mock_do_instance.update_node_pools.assert_called_once_with(4, 10)
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(4)

    def test_starship_launch_scaling(self):
        """Test scaling for Starship launches"""
        # Create Starship launch with multiple programs to trigger Starship logic
        launch_time = timezone.now() + dtime.timedelta(minutes=30)
        self.create_test_launch(
            "Starship Test Flight", launch_time, self.spacex, [self.starship_program, self.other_program]
        )

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should scale to 1 (base) + 5 (Starship) + 1 (other program) = 7 workers
            mock_do_instance.update_node_pools.assert_called_once_with(7, 10)
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(7)

    def test_multiple_launches_scaling(self):
        """Test scaling with multiple launches"""
        launch_time = timezone.now() + dtime.timedelta(minutes=30)

        # SpaceX launch
        self.create_test_launch("Falcon 9 Test", launch_time, self.spacex)

        # ULA launch
        self.create_test_launch("Atlas V Test", launch_time, self.ula)

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should scale to 1 + 3 (SpaceX) + 2 (ULA) = 6 workers
            mock_do_instance.update_node_pools.assert_called_once_with(6, 10)
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(6)

    def test_max_workers_limit(self):
        """Test that max workers limit is respected"""
        launch_time = timezone.now() + dtime.timedelta(minutes=30)

        # Create many launches to exceed max
        for i in range(15):
            self.create_test_launch(f"Test Launch {i}", launch_time, self.spacex)

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should cap at max_workers (10)
            mock_do_instance.update_node_pools.assert_called_once_with(10, 10)
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(10)

    def test_custom_worker_count(self):
        """Test custom worker count override"""
        self.autoscaler_settings.custom_worker_count = 7
        self.autoscaler_settings.save()

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should use custom count regardless of launches
            mock_do_instance.update_node_pools.assert_called_once_with(7, 10)
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(7)

    def test_no_changes_required(self):
        """Test when no node scaling changes are needed (but KEDA still updates)"""
        # Current workers matches expected (1 base worker, no launches)
        self.autoscaler_settings.current_workers = 1
        self.autoscaler_settings.save()

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 1

            check_autoscaler()

            # Node pools should not be updated when no scaling changes needed
            mock_do_instance.update_node_pools.assert_not_called()
            # But KEDA should always be updated with current expected worker count
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(1)

    def test_events_scaling(self):
        """Test scaling for events"""
        event_time = timezone.now() + dtime.timedelta(minutes=30)
        event = Events.objects.create(name="Test Event", date=event_time, description="Test event")
        event.program.add(self.starship_program)

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should scale to 1 (base) + 1 (other_weight for event) + 3 (starship_event_weight) = 5 workers
            mock_do_instance.update_node_pools.assert_called_once_with(5, 10)
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(5)

    def test_24_hour_window_launches(self):
        """Test that launches outside the 24-hour window don't trigger scaling"""
        # Launch in 23 hours - outside the specific 24-hour window (24h-5min to 24h+15min)
        launch_time = timezone.now() + dtime.timedelta(hours=23)
        self.create_test_launch("Future Launch", launch_time, self.spacex)

        with patch("autoscaler.autoscaler.DigitalOceanHelper") as mock_do:
            mock_do_instance = Mock()
            mock_do.return_value = mock_do_instance
            mock_do_instance.get_node_pool_min.return_value = 2

            check_autoscaler()

            # Should scale to 1 (base) only since 23 hours doesn't fall in the 24-hour window
            # The 24-hour window is actually: now+24h-5min to now+24h+15min
            mock_do_instance.update_node_pools.assert_called_once_with(1, 10)
            mock_do_instance.update_keda_min_replicas.assert_called_once_with(1)


class DigitalOceanHelperTests(TestCase):
    def setUp(self):
        self.helper = DigitalOceanHelper()

    @patch("autoscaler.digitalocean_helper.requests.get")
    def test_get_node_pools(self, mock_get):
        """Test getting node pools from DigitalOcean API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "node_pools": [
                {"id": "test-id", "name": "test-pool", "tags": ["scalable"], "min_nodes": 2, "max_nodes": 10}
            ]
        }
        mock_get.return_value = mock_response

        result = self.helper.get_node_pools()

        self.assertEqual(result["node_pools"][0]["name"], "test-pool")
        self.assertIn("scalable", result["node_pools"][0]["tags"])

    @patch("autoscaler.digitalocean_helper.requests.put")
    @patch.object(DigitalOceanHelper, "get_node_pools")
    def test_update_node_pools(self, mock_get_pools, mock_put):
        """Test updating node pools"""
        mock_get_pools.return_value = {
            "node_pools": [
                {
                    "id": "test-id",
                    "name": "test-pool",
                    "tags": ["scalable"],
                    "labels": {},
                    "taints": [],
                    "min_nodes": 2,
                    "max_nodes": 10,
                }
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        self.helper.update_node_pools(5, 15)

        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertEqual(call_args[1]["json"]["min_nodes"], 5)
        self.assertEqual(call_args[1]["json"]["max_nodes"], 15)

    @patch("kubernetes.client.CustomObjectsApi")
    @patch("kubernetes.config.load_incluster_config")
    def test_update_keda_min_replicas(self, mock_config, mock_api_class):
        """Test updating KEDA ScaledObject with realistic pod capacity calculations"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # Mock current ScaledObject
        mock_scaled_object = {"spec": {"minReplicaCount": 3, "maxReplicaCount": 100}}
        mock_api.get_namespaced_custom_object.return_value = mock_scaled_object

        self.helper.update_keda_min_replicas(4)

        # Verify API calls
        mock_api.get_namespaced_custom_object.assert_called_once_with(
            group="keda.sh",
            version="v1alpha1",
            namespace="sln-prod",
            plural="scaledobjects",
            name="spacelaunchnow-web-comprehensive-scaler",
        )

        mock_api.patch_namespaced_custom_object.assert_called_once()

        # Check pod calculations based on realistic capacity:
        # 4 worker nodes * 8 pods per node = 32 min pods
        # 4 worker nodes * 12 pods per node = 48 max pods
        call_args = mock_api.patch_namespaced_custom_object.call_args
        updated_object = call_args[1]["body"]
        self.assertEqual(updated_object["spec"]["minReplicaCount"], 32)  # max(3, 4*8)
        self.assertEqual(updated_object["spec"]["maxReplicaCount"], 48)  # min(100, 4*12)

    @patch("kubernetes.config.load_kube_config")
    @patch("kubernetes.config.load_incluster_config")
    def test_keda_config_fallback(self, mock_incluster, mock_kube_config):
        """Test Kubernetes config fallback"""
        # Simulate in-cluster config failure
        mock_incluster.side_effect = Exception("Not in cluster")

        with patch("kubernetes.client.CustomObjectsApi"):
            self.helper.update_keda_min_replicas(2)

        # Should fallback to local config
        mock_kube_config.assert_called_once()

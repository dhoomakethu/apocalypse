(function() {
    function Controller($scope, $http) {
        $scope.current_state = undefined;
        $scope.selected_event = undefined;
        $scope.event_category = "network";
        $scope.isRefreshing = false;
        $scope.error = false;
        $scope.refreshText = "Refresh Services";
        $scope.model = {
            category: undefined,
            service: undefined,
            event: {
                name: undefined
            }
        };

        $scope.delay_model = {
            service: undefined,
            category: undefined,
            event: {
                name: "network_delay",
                delay: "1s",
                jitter: "100ms",
                distribution: "normal"
            }
        }
        $scope.loss_model = {
            service: undefined,
            category: undefined,
            event: {
                name: "network_loss",
                loss: 10,
                correlation: undefined,
            }
        }
        $scope.corrupt_model = {
            service: undefined,
            category: undefined,
            event: {
                name: "network_corrupt",
                corrupt: 10,
                correlation: undefined,
            }
        }
        $scope.duplicate_model = {
            service: undefined,
            category: undefined,
            event: {
                name: "network_duplicate",
                duplicate: 10,
                correlation: undefined,
            }
        }
        $scope.reorder_model = {
            service: undefined,
            category: undefined,
            event: {
                name: "network_reorder",
                delay: "1s",
                reorder: 25,
                gap: undefined,
                correlation: undefined,
            }
        }
        $scope.burncpu_model = {
            service: undefined,
            category: undefined,
            event: {
                name: "burn_cpu",
                cpuload: 75,
                duration: 100,
                cpu_core: 1

            }
        }
        $scope.burnram_model = {
            service: undefined,
            category: undefined,
            event: {
                name: "burn_ram",
                ramload: 75,
                duration: 100,

            }
        }
        $scope.distribution_list = ["normal", "uninform", "pareto", "paretonormal"];
        $scope.changeBehavior = function() {
            $scope.model.category = $scope.event_category;
            if (this.selected_event == "restore"){
                $scope.restore_network($scope.model);

            }else if (this.selected_event == "delay"){
                $scope.delay_model.service = $scope.model.service;
                $scope.delay_model.category = $scope.event_category;
                $scope.emulate_behavior($scope.delay_model);

            } else if (this.selected_event == "loss"){
                $scope.loss_model.service = $scope.model.service;
                $scope.loss_model.category = $scope.event_category;
                $scope.emulate_behavior($scope.loss_model);

            }else if (this.selected_event == "corrupt"){
                $scope.corrupt_model.service = $scope.model.service;
                $scope.corrupt_model.category = $scope.event_category;
                $scope.emulate_behavior($scope.corrupt_model);

            }else if (this.selected_event == "duplicate"){
                $scope.duplicate_model.service = $scope.model.service;
                $scope.duplicate_model.category = $scope.event_category;
                $scope.emulate_behavior($scope.duplicate_model);

            }else if (this.selected_event == "reorder"){
                $scope.reorder_model.service = $scope.model.service;
                $scope.reorder_model.category = $scope.event_category;
                $scope.emulate_behavior($scope.reorder_model);

            }else if (this.selected_event == "burn_cpu"){
                $scope.burncpu_model.service = $scope.model.service;
                $scope.burncpu_model.category = $scope.event_category;
                $scope.emulate_behavior($scope.burncpu_model);

            }else if (this.selected_event == "burn_ram"){
                $scope.burnram_model.service = $scope.model.service;
                $scope.burnram_model.category = $scope.event_category;
                $scope.emulate_behavior($scope.burnram_model);

            }else {
                $scope.model.event.name = this.selected_event;
                $scope.emulate_behavior($scope.model)
            }

        }
        $scope.get_current = function() {
            $scope.error = false;
            $scope.current_state = "Monkey finding current state!!"
            $http.get('/service_state/'+$scope.model
            .service+'?category='+$scope.event_category)
            .then
            (function
            (response) {
                $scope.current_state = response.data;
                console.log('Successfully retrieved the behavior ', $scope
                .current_behavior);
            }, function(error) {
                $scope.error = error.data.error || error;
            });
        }

        $scope.emulate_behavior = function(_model) {

            // Angular $http() and then() both return promises themselves
            $scope.current_state = "Monkey Working!!";
            $http.post('/emulate', _model).then(function() {
                        console.log('Successfully changed the behavior to', $scope.behavior);
                        $scope.get_current();
                    }, function(error) {
                        $scope.error = error.data.error || error;
                        $scope.current_state = "Something went wrong, Monkey is confused!!";
                    });

        }

        $scope.restore_network = function() {

            // Angular $http() and then() both return promises themselves
            $scope.current_state = "Monkey Working!!";
            $http.post('/restore/'+$scope.model.service).then(function() {
                    console.log('Successfully restored behavior for service',
                    $scope.model.service);
                    $scope.get_current();

                }, function(error) {
                    $scope.error = error.data.error || error;
                    $scope.current_state = "Something went wrong, Monkey is confused!!";
                });

        }

        $scope.refreshServices = function() {
            $scope.isRefreshing = true;
            $scope.refresh_text = "Refreshing...";
            $http.post('/refresh').then(function() {
                        console.log('Successfully Refreshed services');
                        $scope.isRefreshing = false;
                        $scope.refresh_text = "Refresh Services";
                    }, function(error) {
                        $scope.error = error.data.error || error;
                        $scope.isRefreshing = false;
                        $scope.refresh_text = "Refresh Services";
                    });

        }

    }


    angular
        .module('simulator', [])
        .controller('ctrl', Controller);
})();
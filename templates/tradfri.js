angular
  .module("tradfri", [])

  .component("devicesList", {
    templateUrl: "app/tradfri/devices.html",
    controller: function ($scope, tradfri_requests) {
      var self = this;
      this.devicetype = "Light";
  
      this.setFilter = function (filter) {
        self.devicetype = filter;
      }

      tradfri_requests.getDevices()
        .then (function (response) {
          console.log(response);
          self.data = response.data.Devices;
        }, function (response) {
          alert(response);
        })


    }
  })

  .component("tradfriPlugin", {
    templateUrl: "app/tradfri/index.html",
    controller: function (tradfri_requests, $window, $scope) {
      this.counter = 0;
      this.showDevices = 0;
      this.showSetup = 0;

      var self = this;

      tradfri_requests.getRequest("/status")
        .then (function (response) {
          console.log(response)
          self.showDevices = 1;
          
        }, function (response) {
          console.log(response)
          if (response.status == 471) {
            self.showSetup = 1;
          } else {
            $window.alert("Request timed out");
          }
        })

      
      $scope.$on("ShowSetup", function (evt, data) {
          self.showSetup = 1;
          self.showDevices = 0;
      });  
      
      $scope.$on("SetupCompleted", function (evt, data) {
          console.log("SetupCompleted - called");
          self.showSetup = 0;
          self.showDevices = 1;
      });  

      this.setup_clicked = function () {
        $scope.$emit("ShowSetup", "");
      }
    }
  })

  .component("tradfriTest", {
    templateUrl: "app/tradfri/test.html",
    controller: function (tradfri_requests, $window, $scope, $rootScope) {
      this.test = function () {
        console.log("Test clicked");
        $scope.$emit("SetupCompleted", "Some data");
      }

      $scope.$on("TestDown", function (evt, data) {
        console.log("On called");
    });
    }
  })

  .component("configureTradfri", {
    templateUrl: "app/tradfri/setup.html",
    controller: function configureTradfri($scope, $uibModal, tradfri_requests, $window) {

      var testModal = {
        templateUrl: "app/tradfri/deviceRenameModal.html"
      };

      var scope = $scope.$new(true);

      this.submitConfig = function () {
        tradfri_requests.postRequest('setup', {"tradfri-ip": this.ip, "tradfri-key": this.key})
          .then(function (response){
            console.log("Resolved");
            $scope.$emit("SetupCompleted", "");
          }, function (response){
            console.log("Rejected");
            console.log(response);
            $window.alert("Unable to create config, gateway timeout!\nCheck connetion, IP and KEY.");
          })
        
        ;
      };

    }
  });

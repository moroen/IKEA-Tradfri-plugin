angular
  .module("tradfri", [])

  .component("tradfriDevices", {
    templateUrl: "app/tradfri/devices.html",
    controller: function ($scope, tradfri_requests) {
      var self = this;
      this.devicetype = "Light";
      this.isLoaded = false;
  
      this.setFilter = function (filter) {
        self.devicetype = filter;
      }

      tradfri_requests.getDevices()
        .then (function (response) {
          console.log(response);
          self.data = response.data.Devices;
          self.isLoaded = true;
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

      var $ctrl = this;

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

  .component("devicesTable", {
    bindings: {
      devices: '<',
      devicetype:'@',
      onSelect: '&',
      onUpdate: '&'
    },
    template: '<table id="tradfri-devices" class="display" width="100%"></table>',
    controller: function ($element, $scope, tradfri_requests, dataTableDefaultSettings) {
      var $ctrl = this;
      var table;
      
      $ctrl.$onInit = function () {
        console.log("Table onInit");
        console.log($ctrl.text);
        console.log($ctrl.devices);

        table = $element.find('table').dataTable(Object.assign({}, dataTableDefaultSettings, {
          order: [[0, 'asc']],
          columns: [
              { title: 'Id', data: 'DeviceID' },
              { title: 'Name', data: 'Name' },
          ],
        }));

        render($ctrl.devicetype);
      };

      function render (devicetype) {
        console.log("Render called");
        var items;

        tradfri_requests.getDevices()
        .then (function (response) {
          console.log(response.data.Devices);

          items = response.data.Devices
          
          table.api().clear();
          table.api().rows
                .add(items)
                .draw();
        }, function (response) {
          console.log(response)
          if (response.status == 471) {
            $scope.$emit("ShowSetup", "");
          } else {
            $window.alert("Request timed out");
          }
        })

        items = Object.assign({}, {Id: 1, Name: 'Test'});
        console.log(items);   
        
        /*
        table.api().clear();
        table.api().row
                .add(items)
                .draw();
        */
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

angular
  .module("tradfri")

  .factory('tradfri_requests', function ($http, $httpParamSerializerJQLike, $q, $location) {
    var service = {};
  
    service.postRequest = function (uri, data) {
      var deferred = $q.defer();

      $http({ 
        method: 'POST',
        url: `http://${$location.host()}:8085/`+uri,
        data: $httpParamSerializerJQLike(data),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
     }).then(function (response){
        deferred.resolve(response);
     },function (response){
        deferred.reject(response)
     });

      return deferred.promise;
    }

    service.getRequest = function (uri) {
      var deferred = $q.defer();

      $http({ 
        method: 'GET',
        url: `http://${$location.host()}:8085`+uri
     }).then(function (response){
        deferred.resolve(response);
     },function (response){
        deferred.reject(response)
     });

      return deferred.promise;
    }

    service.getDevices = function () {
      var deferred = $q.defer();
   
      $http({
        cache: true,
        method: 'GET',
        url: `http://${$location.host()}:8085/devices`
     }).then(function (response){
        deferred.resolve(response);
     },function (response){
        deferred.reject(response);
     });
      return deferred.promise;
    }
  
    return service;
  })

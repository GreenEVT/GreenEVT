
<?php
// The database with relvant parcel information
$myPDO = new PDO('sqlite:webparcel.db');

if ($_SERVER["REQUEST_METHOD"] == "POST") {
	$sql = "UPDATE webparcels SET householdcount=:count WHERE ogc_fid=:id";
	$query = $myPDO->prepare($sql);
	$query->execute(array(':count' => (int)$_POST["count"], ':id' => (int)$_POST["id"]));
	 if($query->rowCount()) {
   		echo 'saved';
	 } else {
	    print_r($query->errorInfo());
	 }
}


$result = $myPDO->query("SELECT * FROM webparcels WHERE householdcount =-1 LIMIT 1");
$row = $result->fetch();
$address = $row['siteadd'];
$id = $row['ogc_fid'];
$altparno = $row['altparno'];


$result = $myPDO->query("SELECT WKT_GEOMETRY FROM parcelarea WHERE altparno = '".$altparno."'");
$row = $result->fetch();


preg_match_all('/-\d{2}\.\d+ \d{2}\.\d+/',$row['WKT_GEOMETRY'], $matches);

$i = 0;

foreach ($matches[0] as $m) {

  list($long[$i], $lat[$i]) = explode(" ", $m);
  $i++;
}

?>


<!DOCTYPE html>
<html>
  <head>
    <title>Count households</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=default"></script>

    <!-- FILL IN A VALID GOOGLE API KEY HERE -->
    <script src="https://maps.googleapis.com/maps/api/js?key=!!!!!FILLINKEY!!!!!!&callback=initMap&libraries=&v=weekly" defer></script>
    <style type="text/css">
      /* Set the size of the div element that contains the map */
   	#map, #pano {
        float: left;
        height: 500px;
        width: 50%;
      }

    #infobox {
    	float: left;
    	margin-bottom: 60px;
    	width: 100%;
    }
    </style>
    <script>

    	var map;
    	var geocoder;
    	var sv ;
		var geocoder ;
		var directionsService ;
		var panorama;
		var address = <?php
		echo "'".$address. " Greensboro, NC';";
        ?>;
		var myLatLng;
		var map;

     const triangleCoords = [
     <?php
       if (!empty($long)) {
        for($i=0; $i<count($long);$i++) {
        echo "{ lat: ".$lat[$i].", lng: ".$long[$i]." },"; 
      }}
     ?>
     ];


      // Initialize and add the map
      function initMap() {
      	geocoder = new google.maps.Geocoder();
    	sv = new google.maps.StreetViewService();
		geocoder = new google.maps.Geocoder();
		directionsService = new google.maps.DirectionsService();

      	 panorama = new google.maps.StreetViewPanorama(document.getElementById("pano"));



      	  geocoder.geocode({ 'address': address }, function (results, status) {
	        console.log(results);
	        const latLng = {lat: results[0].geometry.location.lat (), lng: results[0].geometry.location.lng ()};
	        console.log (latLng);
	        if (status == 'OK') {

	        	// Put a marker on the map
	        	map = new google.maps.Map(document.getElementById("map"), {
		          zoom: 20,
		          center: latLng,
		        });
		        map.setStreetView(panorama);

	            const marker = new google.maps.Marker({
	                position: latLng,
	                map: map,
	            });


            const parcel = new google.maps.Polygon({
                paths: triangleCoords,
                strokeColor: "#FF0000",
                strokeOpacity: 0.8,
                strokeWeight: 2,
                fillColor: "#FF0000",
                fillOpacity: 0.35,
              });
              parcel.setMap(map);

	             // find a Streetview location on the road
			     var request = {
			        origin: address,
			        destination: address,
			        travelMode: google.maps.DirectionsTravelMode.DRIVING
			     };
			     directionsService.route(request, directionsCallback);
	            console.log (map);
	        } else {
	            alert('Geocode was not successful for the following reason: ' + status);
	        }
   		});

        

      }
function processSVData(data, status) {
  if (status == google.maps.StreetViewStatus.OK) {

    panorama.setPano(data.location.pano);

    var heading = google.maps.geometry.spherical.computeHeading(data.location.latLng, myLatLng);
    panorama.setPov({
      heading: heading,
      pitch: 0,
      zoom: 1
    });
    panorama.setVisible(true);

  } else {
    alert("Street View data not found for this location.");
  }
}

function directionsCallback(response, status) {
  if (status == google.maps.DirectionsStatus.OK) {
    var latlng = response.routes[0].legs[0].start_location;
    sv.getPanoramaByLocation(latlng, 50, processSVData);
  } else {
    alert("Directions service not successfull for the following reason:" + status);
  }
}
    </script>
  </head>
  <body>
    <h1>Count the number of households</h1>
    If not anything is found, enter 0. If you are unsure, enter -2.
    <br /><br />


    <div id="infobox">
   <h2> <?php echo $address; ?></h2>


   <form method="post" action="<?php echo $_SERVER["PHP_SELF"];?>">
   	<input type="hidden" name="id" value="<?php echo $id; ?>">
   	Enter number of households: <input type="text" name="count"> <input type="submit">
   </form>


  <?php
		$result = $myPDO->query("SELECT COUNT(*) FROM webparcels WHERE householdcount =-1");
		$row = $result->fetch();
		echo "Remaining parcels to classify: ".$row[0];

  ?>
    </div>
	
    <!--The div element for the map -->
    <div id="mapsdisplay">
    <div id="map"></div>
    <div id="pano"></div>
    <div>

  </body>
</html>

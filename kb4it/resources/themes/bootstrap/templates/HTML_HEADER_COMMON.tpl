<!DOCTYPE Html>
<html lang="en">
<head>
    <title>KB4IT - ${var['title'][0]}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="Asciidoctor 2.0.10">
    <meta name="description" content="KB4IT document">
    <meta name="author" content="KB4IT by t00mlabs.net">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="${var['theme']['path']}/framework/bootstrap/css/bootstrap.min.css" />
    <link rel="stylesheet" href="${var['theme']['path']}/framework/bootstrap/js/bootstrap.bundle.min.js" />
    <link rel="stylesheet" href="${var['theme']['path']}/framework/DataTables/datatables.min.css" type="text/css"/>
    <link rel="stylesheet" href="${var['theme']['path']}/framework/sbadmin/css/sb-admin-2.min.css">
    <script type="text/javascript" src="${var['theme']['path']}/framework/DataTables/datatables.min.js"></script>
    <script type="text/javascript" class="init">
        $(document).ready(function() {
            var data = [];
            for ( var i=0 ; i<50000 ; i++ ) {
                data.push( [ i, i, i, i, i ] );
            }
            $('#kb4it-datatable').DataTable( {
                //~ "dom": '<"top"i>rt<"bottom"flp><"clear">',
                serverSide: false,
                ordering: true,
                searching: true,
                data:           data,
                deferRender:    true,
                scrollY:        500,
                scrollCollapse: true,
                scroller:       true,
                stateSave: true,
                paging:   true,
                info:     true
            } );
        } );
    </script>
</head>
<body class="">
<div class="container-lg">
    <div class="vstack gap-3">
      <div class="bg-light border" id="navbarToggleExternalContent"> <!-- 1st -->
       <nav class="navbar fixed-top navbar-expand-lg navbar-light bg-light">
          <div class="container-fluid">
                <a class="navbar-brand" href="#"><img src="${var['theme']['path']}/images/logo.png" class="hover-shadow hover-zoom"></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
              <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarSupportedContent">
              <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item">
                  <a class="nav-link active" aria-current="page" href="#">Home</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#">Link</a>
                </li>
                <li class="nav-item dropdown">
                  <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                    Dropdown
                  </a>
                  <ul class="dropdown-menu" aria-labelledby="navbarDropdown">
                    <li><a class="dropdown-item" href="#">Action</a></li>
                    <li><a class="dropdown-item" href="#">Another action</a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item" href="#">Something else here</a></li>
                  </ul>
                </li>
                <li class="nav-item">
                  <a class="nav-link disabled">Disabled</a>
                </li>
              </ul>
              <form class="d-flex">
                <input class="form-control me-2" type="search" placeholder="Search" aria-label="Search">
                <button class="btn btn-outline-success" type="submit">Search</button>
              </form>
            </div>
          </div>
       </nav> 
      </div>
      <div class="bg-light border"> <!-- 2nd -->
        <div class="accordion" id="accordionExample">
          <div class="accordion-item">
            <h2 class="accordion-header" id="headingOne">
              <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
                Accordion Item #1
              </button>
            </h2>
            <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="headingOne" data-bs-parent="#accordionExample">
              <div class="accordion-body">
                <table id="kb4it-datatable" class="table table-striped display nowrap stripe compact" style="width:90%" data-page-length="50" >
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>First name</th>
                            <th>Last name</th>
                            <th>ZIP / Post code</th>
                            <th>Country</th>
                        </tr>
                    </thead>
                </table>
              </div>
            </div>
          </div>
          <div class="accordion-item">
            <h2 class="accordion-header" id="headingTwo">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                Accordion Item #2
              </button>
            </h2>
            <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="headingTwo" data-bs-parent="#accordionExample">
              <div class="accordion-body">
                <strong>This is the second item's accordion body.</strong> It is hidden by default, until the collapse plugin adds the appropriate classes that we use to style each element. These classes control the overall appearance, as well as the showing and hiding via CSS transitions. You can modify any of this with custom CSS or overriding our default variables. It's also worth noting that just about any HTML can go within the <code>.accordion-body</code>, though the transition does limit overflow.
              </div>
            </div>
          </div>
          <div class="accordion-item">
            <h2 class="accordion-header" id="headingThree">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
                Accordion Item #3
              </button>
            </h2>
            <div id="collapseThree" class="accordion-collapse collapse" aria-labelledby="headingThree" data-bs-parent="#accordionExample">
              <div class="accordion-body">
                <strong>This is the third item's accordion body.</strong> It is hidden by default, until the collapse plugin adds the appropriate classes that we use to style each element. These classes control the overall appearance, as well as the showing and hiding via CSS transitions. You can modify any of this with custom CSS or overriding our default variables. It's also worth noting that just about any HTML can go within the <code>.accordion-body</code>, though the transition does limit overflow.
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="bg-light border">Third item</div> <!-- 3rd -->
    </div>
</div>

var listOfGRLCRepos = [];
// It is possible to increase the maximum number of requests by supplying a
// client_id and client_secret https://developer.github.com/v3/oauth_authorizations/
var gh_auth = ''; //'?client_id=xxx&client_secret=yyy';
var currRepo = '';

function fetchGrlcRepos() {
  listOfGRLCRepos = [];
  var user = $('#gh_username').val();
  var url = 'https://api.github.com/users/' + user + '/repos' + gh_auth;
  $.ajax({
    url: url
  }).done(function(repos) {
    $.each(repos, listFiles);
  });
}

function listFiles(idx, repo) {
  var url = 'https://api.github.com/repos/' + repo.full_name + '/contents' + gh_auth;
  $.ajax({
    url: url
  }).done(function(files) {
    currRepo = repo.full_name;
    for(var i = 0; i < files.length; i++) {
      if(isSparql(files[i])) {
        listOfGRLCRepos.push(currRepo);
        break;
      }
    }
    displayRepos(listOfGRLCRepos);
  });
}

function isSparql(file) {
  var filename = file.name;
  return filename.endsWith('.rq') || filename.endsWith('.sparql');
}

function displayRepos(grlcRepos) {
  $('#resultset').html('');
  for(repoId in grlcRepos) {
    var repo = grlcRepos[repoId];
    var link = "<a href='http://grlc.io/api/" + repo + "'>" + repo  + "</a><br>";
    $('#resultset').append(link);
  }
}

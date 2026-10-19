//==============================================================================
// standalone.js
//==============================================================================

indexing = false;
dataindexing = false;
ruleindexing = true;

var game = 'buttonsandlights';
var role = 'robot';
var startclock = 10;
var playclock = 10;

var library = [];
var roles = ['robot'];
var state = [];
var statelog = [];
var movelog = [];

function initialize ()
 {document.addEventListener('keydown',handlekey);
  definerules(library,readdata(document.getElementById('library').textContent));
  roles = findroles(library);
  state = findinits(library);
  statelog = [state];
  movelog = [];
  movenum = 0;
  showstate(state);
  showactions(state);
  showhistory(movelog,state);
  return true}

//==============================================================================

function showstate (state)
 {var stateholder = document.getElementById('stateholder');
  var n = stateholder.childNodes.length;
  for (var i=0; i<n; i++) {stateholder.removeChild(stateholder.childNodes[0])};
  stateholder.appendChild(rendersituation(state));
  return true}

function rendersituation (state)
 {return renderstate(state)}

function renderstate (state)	
 {var widget = document.createElement('textarea');
  widget.setAttribute('rows','12');
  widget.setAttribute('cols','40');
  widget.setAttribute('style','font-family:courier');
  widget.setAttribute('disabled',true);
  widget.value = grindem(state);
  return widget}

//==============================================================================

function showactions (state)
 {var actionholder = document.getElementById('actionholder');
  var n = actionholder.childNodes.length;
  for (var i=0; i<n; i++) {actionholder.removeChild(actionholder.childNodes[0])};
  actionholder.appendChild(renderactions(state));
  return true}

function renderactions (state)
 {var widget = document.createElement('select');
  var option = document.createElement('option');
  option.value = 'error';
  option.text = '';
  widget.add(option);
  var actions = findlegals(state,library).sort();
  for (var i=0; i<actions.length; i++)
      {var option = document.createElement('option');
       var value = grind(actions[i]);
       option.value = value;
       option.text = value;
       widget.add(option)}
  if (findterminalp(state,library)) {widget.disabled = true}
     else {widget.disabled = false};
  widget.setAttribute('onchange','perform(read(this.value))');
  return widget}

//==============================================================================

function showhistory (moves,state)
 {var widget = document.getElementById('history');
  var n = widget.childNodes.length;
  for (var i=0; i<n; i++) {widget.removeChild(widget.childNodes[0])};
  widget.appendChild(renderhistory(moves,state));
  return true}

function renderhistory (moves,state)
 {var widget = document.createElement('table');
  widget.setAttribute('cellspacing',0);
  widget.setAttribute('cellpadding',3);
  widget.setAttribute('border',1);
  var row = widget.insertRow(0);
  var cell = row.insertCell(0);
  cell.innerHTML = 'Step';
  cell.setAttribute('width','120');
  cell.setAttribute('align','center');
  cell.setAttribute('style','font-weight:bold');
  cell.setAttribute('bgcolor','#dddddd');
  for (var j=0; j<roles.length; j++)
      {cell = row.insertCell(j+1);
       cell.innerHTML = roles[j];
       cell.setAttribute('width','120');
       cell.setAttribute('align','center');
       cell.setAttribute('style','font-weight:bold');
       cell.setAttribute('bgcolor','#dddddd')};

  for (var i=0; i<movenum; i++)
      {row = widget.insertRow(i+1);
       cell = row.insertCell(0);
       cell.setAttribute('align','center');
       cell.setAttribute('bgcolor','#dddddd');
       cell.innerHTML = i+1;
       for (var j=0; j<roles.length; j++)
           {cell = row.insertCell(j+1);
            cell.setAttribute('width','120');
            cell.setAttribute('align','center');
            if (findcontrol(statelog[i],library)===roles[j])
               {cell.innerHTML = grind(moves[i])}}};

  row = widget.insertRow(widget.rows.length);
  cell = row.insertCell(0);
  cell.innerHTML = 'Score';
  cell.setAttribute('style','font-weight:bold');
  cell.setAttribute('bgcolor','#dddddd');
  cell.setAttribute('align','center');
  for (var i=0; i<roles.length; i++)
      {cell = row.insertCell(i+1);
       cell.setAttribute('align','center');
       cell.setAttribute('bgcolor','#dddddd');
       cell.innerHTML = findreward(roles[i],state,library)};
  return widget}

//==============================================================================

function perform (action)
 {if (action==='error') {return false};
  statelog = statelog.slice(0,movenum+1);
  movelog = movelog.slice(0,movenum);
  movelog.push(action);
  state = copy(state);
  compexecute(action,state,library);
  statelog.push(state);
  movenum++;
  showstate(state);
  showactions(state);
  showhistory(movelog,state);
  return true}

function up ()
 {if (movenum<=0) {return false};
  movenum--;
  state = statelog[movenum];
  showstate(state);
  showactions(state);
  showhistory(movelog,state);
  return true}

function dn ()
 {if (movenum>=movelog.length) {return false};
  movenum++;
  state = statelog[movenum];
  showstate(state);
  showactions(state);
  showhistory(movelog,state);
  return true}

function copy (obj)
 {return obj.slice(0)}

//------------------------------------------------------------------------------
// handlekey
//------------------------------------------------------------------------------

function handlekey (e)
 {if (e.keyCode == '37') {e.preventDefault(); up()};
  if (e.keyCode == '38') {e.preventDefault(); up()};
  if (e.keyCode == '39') {e.preventDefault(); dn()};
  if (e.keyCode == '40') {e.preventDefault(); dn()};
  return false}

//==============================================================================
// Basics
//==============================================================================

function findroles (rules)
 {return compfinds('R',seq('role','R'),seq(),rules)}

function findbases (rules)
 {return compfinds('P',seq('base','P'),seq(),rules)}

function findactions (rules)
 {return compfinds('A',seq('action','A'),seq(),rules)}

function findinits (rules)
 {return compfinds('P',seq('init','P'),seq(),rules)}

function findcontrol (facts,rules)
 {return compfindx('X',seq('control','X'),facts,rules)}

function findlegalp (move,facts,rules)
 {return compfindp(seq('legal',move),facts,rules)}

function findlegalx (facts,rules)
 {return compfindx('X',seq('legal','X'),facts,rules)}

function findlegals (facts,rules)
 {return compfinds('X',seq('legal','X'),facts,rules)}

function findreward (role,facts,rules)
 {var value = compfindx('R',seq('goal',role,'R'),facts,rules);
  if (value) {return value};
  return 0}

function findterminalp (facts,rules)
 {return compfindp('terminal',facts,rules)}

//==============================================================================
//==============================================================================
//==============================================================================


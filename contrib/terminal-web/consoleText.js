/*    Web-page console v0.1, consoleText.js    Copyright (C) 2009 Richard Tew <richard.m.tew@gmail.com>    Donate if you appreciate it: http://disinterest.org/donate.html
    This program is free software: you can redistribute it and/or modify    it under the terms of the GNU General Public License as published by    the Free Software Foundation, either version 3 of the License, or    (at your option) any later version.
    This program is distributed in the hope that it will be useful,    but WITHOUT ANY WARRANTY; without even the implied warranty of    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
// CONSTANTS
// GLOBALS
var consoleTextElement = null;
var promptHTML = "<span class='prompt'>&gt;</span>";var cursorHTML = "<span id='cursor' class='cursor'>&nbsp;</span>";
var consoleBufferHTML = "";var consoleLineArray = [ ];
var cursorLineIndex = 0;
var lastKeyCode = undefined;
// CODE
function blinkCursor() {  // Whatever element on the page is tagged as the cursor gets blinked.  cursorElement = document.getElementById("cursor");  if (cursorElement != null) {    if (cursorElement.getAttribute("className") == "cursor") { // Hide the cursor.      cursorElement.setAttribute("class", "");      cursorElement.setAttribute("className", "");    } else { // Show the cursor.      cursorElement.setAttribute("class", "cursor");      cursorElement.setAttribute("className", "cursor");    }  }
  setTimeout("blinkCursor()", 500);}
function printHTML(html) {  // If the cursor has been moved into the already entered text, then  // whatever is typed will be inserted at the cursor position.  Otherwise  // it will be added to the end of the line.  if (cursorLineIndex) {    consoleLineArray.splice(consoleLineArray.length - cursorLineIndex, 0, html);  } else    consoleLineArray.push(html);
  updateConsole();}
function printCarriageReturn() {  // As we have no history tracking at this stage, we lump the gathered text  // for the current line into the accumulated buffer and start a new line.  consoleBufferHTML += promptHTML + consoleLineArray.join("") + "<br>";  consoleLineArray = [ ];  cursorLineIndex = 0;
  updateConsole();}
function printDelete() {  if (consoleLineArray.length) {    if (cursorLineIndex) {      // We want to remove under the cursor.  The cursor should stay in the      // same place, and the text following it should move towards it.      consoleLineArray.splice(consoleLineArray.length - cursorLineIndex, 1);      cursorLineIndex -= 1;    }
    updateConsole();  }}
function printBackspace() {  if (consoleLineArray.length) {    if (cursorLineIndex == 0) {      // Just remove the last entry as the cursor is at the end of the line.      consoleLineArray.pop();    } else if (cursorLineIndex < consoleLineArray.length) {      // We want to remove from the left of the cursor, so minus one.      consoleLineArray.splice(consoleLineArray.length - cursorLineIndex - 1, 1);    }
    updateConsole();  }}
function moveCursor(direction) {  // Our index is from the right hand side, so the direction is reversed.  cursorLineIndex += -direction;  // Bounds check the cursor position.  if (cursorLineIndex < 0)    cursorLineIndex = 0;  else if (cursorLineIndex > consoleLineArray.length)    cursorLineIndex = consoleLineArray.length;
  // Updating the console will display the cursor in the correct position.  updateConsole();}
function updateConsole() {  var lineArray = consoleLineArray;  var trailingHTML = cursorHTML;
  if (cursorLineIndex) {    // Copy the current line array and make the select entry the cursor too.    var idx = lineArray.length - cursorLineIndex;    lineArray = lineArray.slice(0);    lineArray[idx] = "<span id='cursor' class='cursor'>"+ lineArray[idx] +"</span>";    // Prevent the real cursor from being added.    trailingHTML = "";  }
  // Compose the currently displayed line.  consoleTextElement.innerHTML = consoleBufferHTML + promptHTML + lineArray.join("") + trailingHTML;  consoleTextElement.parentNode.scrollTop = 1000000;}

function handleSpecialKeyPress(keyCode, ctrlKey, altKey, shiftKey) {
  if (ctrlKey || altKey)
    return true;

  // console.log("KeyDown %d %d %d %d", keyCode, ctrlKey, altKey, shiftKey);

  if (keyCode == 46) { // Del
    printDelete();
  } else if (keyCode == 37) { // Arrow left
    moveCursor(-1);
  } else if (keyCode == 39) { // Arrow right
    moveCursor(1);
  } else if (keyCode == 8) { // Backspace 
    printBackspace();
  } else { // NOT HANDLED...
    return true;
  }

  return false;
}
function handleNormalKeyPress(keyCode, ctrlKey, altKey, shiftKey) {  if (ctrlKey || altKey)    return true;

  // console.log("KeyPress %d %d %d %d", keyCode, ctrlKey, altKey, shiftKey);

  if (keyCode == 13) { // CR
    printCarriageReturn();
  } else {
    if (keyCode < 32)
      return true;

    keyCharacter = String.fromCharCode(keyCode);
    printHTML(keyCharacter);
  }

  return false;
}  function onKeyDown(event) {  lastKeyCode = event.keyCode;
	  return handleSpecialKeyPress(lastKeyCode, event.ctrlKey, event.altKey, event.shiftKey);}
function onKeyUp(event) {  lastKeyCode = undefined;  return true;}
function onKeyPress(event) {	
  // Ignore special key handling.
  if (event.which == 0)
    return true;

  return handleNormalKeyPress(event.which || event.keyCode, event.ctrlKey, event.altKey, event.shiftKey);
}
function onPageLoaded() {  onPageLoaded_Window();
  consoleTextElement = document.getElementById("consolebody");
  updateConsole();
  setTimeout("blinkCursor()", 300);}

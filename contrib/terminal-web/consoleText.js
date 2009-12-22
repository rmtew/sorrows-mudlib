/*
    Web-page console v0.1, consoleText.js
    Copyright (C) 2009 Richard Tew <richard.m.tew@gmail.com>
    Donate if you appreciate it: http://disinterest.org/donate.html

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

  // CONSTANTS

  var cursorColor = "rgb(241,128,22)";

  // GLOBALS

  var consoleTextElement = null;

  var promptHTML = "<font class='prompt'>&gt;</font>";
  var cursorHTML = "<font id='cursor' class='inverse'>&nbsp;</font>";

  var consoleBufferHTML = "";
  var consoleLineArray = [ ];

  var cursorLineIndex = 0;
  var cursorVisible = false;

  var lastKeyCode = undefined;

  // CODE

  function blinkCursor() {
    // Whatever element on the page is tagged as the cursor gets blinked.
    cursorElement = document.getElementById("cursor");
    if (cursorElement != null) {
      if (cursorVisible) {
        cursorElement.style.color = color1;
        cursorElement.style.backgroundColor = color2;
      } else {
        cursorElement.style.color = color2;
        cursorElement.style.backgroundColor = cursorColor;
      }
      cursorVisible = !cursorVisible;
    }

    setTimeout("blinkCursor()", 500);
  }

  function printHTML(html) {
    // If the cursor has been moved into the already entered text, then
    // whatever is typed will be inserted at the cursor position.  Otherwise
    // it will be added to the end of the line.
    if (cursorLineIndex) {
      consoleLineArray.splice(consoleLineArray.length - cursorLineIndex, 0, html);
    } else
      consoleLineArray.push(html);

    updateConsole();
  }

  function printCarriageReturn() {
    // As we have no history tracking at this stage, we lump the gathered text
    // for the current line into the accumulated buffer and start a new line.
    consoleBufferHTML += promptHTML + consoleLineArray.join("") + "<br>";
    consoleLineArray = [ ];
    cursorLineIndex = 0;

    updateConsole();
  }

  function printDelete() {
    if (consoleLineArray.length) {
      if (cursorLineIndex) {
        // We want to remove under the cursor.  The cursor should stay in the
        // same place, and the text following it should move towards it.
        consoleLineArray.splice(consoleLineArray.length - cursorLineIndex, 1);
        cursorLineIndex -= 1;
      }

      updateConsole();
    }
  }

  function printBackspace() {
    if (consoleLineArray.length) {
      if (cursorLineIndex == 0) {
        // Just remove the last entry as the cursor is at the end of the line.
        consoleLineArray.pop();
      } else if (cursorLineIndex < consoleLineArray.length) {
        // We want to remove from the left of the cursor, so minus one.
        consoleLineArray.splice(consoleLineArray.length - cursorLineIndex - 1, 1);
      }

      updateConsole();
    }
  }

  function moveCursor(direction) {
    // Our index is from the right hand side, so the direction is reversed.
  	cursorLineIndex += -direction;
  	// Bounds check the cursor position.
  	if (cursorLineIndex < 0)
  	  cursorLineIndex = 0;
  	else if (cursorLineIndex > consoleLineArray.length)
  	  cursorLineIndex = consoleLineArray.length;

    // Updating the console will display the cursor in the correct position.
    updateConsole();
  }

  function updateConsole() {
    var lineArray = consoleLineArray;
    var trailingHTML = cursorHTML;

    if (cursorLineIndex) {
      // Copy the current line array and make the select entry the cursor too.
      var idx = lineArray.length - cursorLineIndex;
      lineArray = lineArray.slice(0);
      lineArray[idx] = "<font id='cursor' class='inverse'>"+ lineArray[idx] +"</font>";
      // Prevent the real cursor from being added.
      trailingHTML = "";
    }

    // Compose the currently displayed line.
    consoleTextElement.innerHTML = consoleBufferHTML + promptHTML + lineArray.join("") + trailingHTML;
    consoleTextElement.parentNode.scrollTop = 1000000;
  }

  function handleKeyPress(keyCode, ctrlKey, altKey, shiftKey) {
    // console.log("Handle %d %d %d %d", keyCode, ctrlKey, altKey, shiftKey);

    if (ctrlKey || altKey)
      return true;


    if (keyCode == 46) { // Del
      printDelete();
    } else if (keyCode == 37) { // Arrow left
      moveCursor(-1);
    } else if (keyCode == 39) { // Arrow right
      moveCursor(1);
    } else if (keyCode == 13) { // CR
      printCarriageReturn();
    } else if (keyCode == 8) { // Backspace 
      printBackspace();
    } else {
      if (keyCode != 32 && keyCode < 48)
        return true;

      keyCharacter = String.fromCharCode(keyCode);
      //if (shiftKey == 0)
      //  keyCharacter = keyCharacter.toLowerCase();
      printHTML(keyCharacter);
    }

    return false;
  }

  function onKeyDown(event) {
    lastKeyCode = event.keyCode;
    // console.log("onKeyDown which %s keyCode %d", event.which, event.keyCode);
    return handleKeyPress(lastKeyCode, event.ctrlKey, event.altKey, event.shiftKey);
  }

  function onKeyUp(event) {
    lastKeyCode = undefined;
    // console.log("onKeyUp which %s keyCode %d", event.which, event.keyCode);
    return true;
  }

  function onKeyPress(event) {
    var keyCode;
    var keyCharacter;

    if (event.which == 0) {
      // Special key handling...
      keyCode = event.keyCode;

      if (keyCode == 46) { // Del
        printDelete();
      } else if (keyCode == 37) { // Arrow left
        moveCursor(-1);
      } else if (keyCode == 39) { // Arrow right
        moveCursor(1);
      } // else
      //console.log("Unhandled raw key code: "+ keyCode.toString());

      //console.log("NORMAL which %s keyCode %d", event.which, event.keyCode);
      return false;
    }

    // Let things like refresh, copy, paste and so forth fall through.
    if (event.ctrlKey)
      return true;

    // Normal key handling...
    if (event.which == undefined) {
      keyCode = event.keyCode // Internet Explorer.
    } else {
      keyCode = event.which // Firefox.
    }

    if (keyCode == 13) { // CR
      printCarriageReturn();
    } else if (keyCode == 8) { // Backspace 
      printBackspace();
    } else {
      keyCharacter = String.fromCharCode(keyCode);

      // console.log("NORMAL which %s keyCode %d char %s", event.which, event.keyCode, keyCharacter);
      printHTML(keyCharacter);
    }

    return false;
  }

  function onPageLoaded() {
    onPageLoaded_Window();

    consoleTextElement = document.getElementById("consoletext");

    updateConsole();

    setTimeout("blinkCursor()", 300);
  }

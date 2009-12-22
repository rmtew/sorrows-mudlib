/*
    Web-page console v0.1, consoleWindow.js
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

var consoleElement;
var draggingConsole = false;

var color1 = "rgb(255,255,255)";
var color2 = "rgb(119,153,204)";

var lastPageX = 0;
var lastPageY = 0;

function onMouseDown(event) {
  if (event.target)
    titleBarElement = event.target; // Firefox.
  else
    titleBarElement = event.srcElement; // Internet Explorer.

  if (titleBarElement.parentNode != consoleElement)
    return true;

  draggingConsole = true;
  consoleElement.style.cursor = 'move';

  // Store initial cursor locations for the deltas to work from.
  lastPageX = event.clientX;
  lastPageY = event.clientY;

  return false;
}

function onMouseUp(event) {
  if (draggingConsole) {
    draggingConsole = false;
    consoleElement.style.cursor = 'auto';
    return false;
  }

  return true;
}

function onMouseMove(event) {
  if (draggingConsole) {
  	var deltaX = event.clientX - lastPageX;
  	var deltaY = event.clientY - lastPageY;

    // Move the console, but ensure we do not allow it to move too far.

  	if (deltaX > 0 || (consoleElement.offsetLeft + deltaX) > 0)
	  consoleElement.style.left = (consoleElement.offsetLeft + deltaX) +"px";

  	if (deltaY > 0 || (consoleElement.offsetTop + deltaY) > 0)
	  consoleElement.style.top = (consoleElement.offsetTop + deltaY) +"px";

    // Record the current mouse positions for the next deltas.
    lastPageX = event.clientX;
    lastPageY = event.clientY;

    return false;
  }
  
  return true;
}

function onPageLoaded_Window() {
  consoleElement = document.getElementById("console");
}


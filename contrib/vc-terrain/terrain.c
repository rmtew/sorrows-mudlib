/*
gcc fractalmodule.c noise.c -I/usr/include/python2.0 -fpic -shared -o fractal.so
*/

#include "Python.h"
#include <math.h>

float noise3(float vec[3]);
void set_noise_seed(int new_seed);

/* Module fractal */

static PyObject *noise_noise3(PyObject *self, PyObject *args) {
	float vec[3], result;

	if (!PyArg_Parse(args, "(fff)", &vec[0], &vec[1], &vec[2])) {
			return NULL;
	}
	result = noise3(vec);
	return Py_BuildValue("f", result);
}

static PyObject *noise_fBm(PyObject *self, PyObject *args) {
	int octaveCount, i;
	float vec[3], result;
	float fWeight;

	if (!PyArg_Parse(args, "(ifff)", &octaveCount, &vec[0], &vec[1], &vec[2])) {
			return NULL;
	}

    result = 0.0f;
    fWeight = 1.0f;

    for (i=0; i<octaveCount; i++) {
        result += noise3(vec) * fWeight;
        fWeight *= 0.5f;

		vec[0] *= 2.0f;
		vec[1] *= 2.0f;
		vec[2] *= 2.0f;
	}

	return Py_BuildValue("f", result);
}

static PyObject *noise_set_seed(PyObject *self, PyObject *args) {
	int new_seed;

	if (!PyArg_Parse(args, "(i)", &new_seed)) {
			return NULL;
	}
	set_noise_seed(new_seed);
	/* Too lazy to look into returning nothing. */
	return Py_BuildValue("i", new_seed);
}

static PyMethodDef fractal_methods[] = {
	{"fBm", noise_fBm, METH_VARARGS},
	{"noise3", noise_noise3, METH_VARARGS},
	{"SetSeed", noise_set_seed, METH_VARARGS},
	{NULL, NULL}           /* sentinel */
};

DL_EXPORT(void)
initterrain(void) {
	Py_InitModule("terrain", fractal_methods);
}

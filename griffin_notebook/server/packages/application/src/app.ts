// Copyright (c) Griffin Project Contributors.
// Distributed under the terms of the Modified BSD License.

import { NotebookApp } from '@jupyter-notebook/application';

import { GriffinNotebookShell } from './shell';

/**
 * App is the main application class. It is instantiated once and shared.
 *
 * Changes from Jupyter Notebook:
 * - Use our GriffinNotebookShell instead of Jupyter's NotebookShell
 */
export class GriffinNotebookApp extends NotebookApp {
  /**
   * Construct a new GriffinNotebookApp object.
   *
   * @param options The instantiation options for an application.
   */
  constructor(options: NotebookApp.IOptions = { shell: new GriffinNotebookShell() }) {
    super({ ...options, shell: options.shell ?? new GriffinNotebookShell() });
  }
}

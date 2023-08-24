import { Application } from '@hotwired/stimulus';

import BookController from './controllers/book_controller';

window.Stimulus = Application.start();
Stimulus.register('book', BookController);

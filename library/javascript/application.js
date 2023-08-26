import { Application } from '@hotwired/stimulus';

import BookController from './controllers/book_controller';
import InfiniteScrollController from './controllers/infinite_scroll_controller';

window.Stimulus = Application.start();
Stimulus.register('book', BookController);
Stimulus.register('infinite-scroll', InfiniteScrollController);

Changelog
=========

0.3 (2025-10-13)
----------------

* Add `get_field` and `get_fields` methods to VirtualModel meta class (smark-1)
* Add dedicated `DoesNotExist` and `MultipleObjectsReturned` exceptions on VirtualModel
* Implement equality on VirtualModel based on ID
* Make properties `start` and `stop` available in addition to `offset` and `limit`
* Short-circuit queries if running on an empty slice
* Fix: When retrieving by index, use a single-item slice instead of running the full query


0.2 (2023-09-05)
----------------

* Introduce virtual models as a closer drop-in replacement for model classes
* Support `detail_url` endpoints on `APIQuerySet` for retrieving individual records
* Implement `in_bulk` on `APIQuerySet`
* Allow customising HTTP headers on `APIQuerySet`
* Documentation


0.1 (2023-05-30)
----------------

* Initial release

<h1 align="center">Hydra DB Growth</h1>

A way to test the growth of a db (mysql, postgresql, ...) when running
Hydra. This is specifically related to this issue: https://github.com/ory/hydra/issues/1574.

### Milestones

- [ ] Graphs (time-series plot) of database size and other meta info
- [ ] Easy Failure rate adjustment via cli
- [ ] Maybe extend the software to allow more tests of the different use cases of Hydra (currently login request failure is observed)

### What seems to be the issue

Users aren't finishing the Login flow - causing tables `hydra_oauth2_authentication_request` and `hydra_oauth2_authentication_session` to explode in size.

### What is failure rate?

The rate at which clients do not complete the login flow.

According to https://github.com/ory/hydra/issues/1574#issuecomment-771573626 it seems out
of 4000 login requests only 100 complete.


### Running the test

(please note this is still incomplete)

    ./scripts/build.sh
    ./scripts/test.sh

Then there should be a UI running on http://127.0.0.1:3000.

Cleanup

    ./scripts/cleanup.sh
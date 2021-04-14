# Changelog

## [v1.1.0](https://github.com/NASA-PDS/pds-doi-service/tree/v1.1.0) (2021-04-13)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/v1.1.0-dev...v1.1.0)

**Improvements:**

- Update DOI UI and Service with new workflow for operational deployment [\#125](https://github.com/NASA-PDS/pds-doi-service/issues/125)

**Defects:**

- site\_url error when we submit on OSTI test server [\#168](https://github.com/NASA-PDS/pds-doi-service/issues/168)
- The url /dois/{lidvid} should still return XML in the record attribute [\#159](https://github.com/NASA-PDS/pds-doi-service/issues/159)
- draft OSTI label [\#154](https://github.com/NASA-PDS/pds-doi-service/issues/154)
- when doing draft with warnings \(e.g. duplicated title\) the -f option does not help [\#150](https://github.com/NASA-PDS/pds-doi-service/issues/150)
- when release command keywords are broken with encoded characters [\#143](https://github.com/NASA-PDS/pds-doi-service/issues/143)
- api does not ignore '/' at the end of url [\#141](https://github.com/NASA-PDS/pds-doi-service/issues/141)
- Raise a specific exception when the OSTI server is not reachable [\#119](https://github.com/NASA-PDS/pds-doi-service/issues/119)

**Other closed issues:**

- As an API user I want to filter on lidvids with wildcards [\#177](https://github.com/NASA-PDS/pds-doi-service/issues/177)
- Analyze/Test the dataCite API for dataCite [\#170](https://github.com/NASA-PDS/pds-doi-service/issues/170)
- As a user, I want to see the lidvid of my DOIs in the email report [\#167](https://github.com/NASA-PDS/pds-doi-service/issues/167)
- Add service to API for update of the status of records with OSTI \(check sub command\) [\#165](https://github.com/NASA-PDS/pds-doi-service/issues/165)
- Implement Application Server to wrap Flask service [\#162](https://github.com/NASA-PDS/pds-doi-service/issues/162)
- When a pds4 label or osti can not be parsed generate error 400 in API [\#157](https://github.com/NASA-PDS/pds-doi-service/issues/157)
- API POST /dois should accept DOI OSTI format in payload [\#148](https://github.com/NASA-PDS/pds-doi-service/issues/148)
- enable filter by status in sub-action 'pds-doi-cmd list' [\#144](https://github.com/NASA-PDS/pds-doi-service/issues/144)
- Update submission to OSTI to handle the removal of a field from the OSTI metadata [\#140](https://github.com/NASA-PDS/pds-doi-service/issues/140)

## [v1.1.0-dev](https://github.com/NASA-PDS/pds-doi-service/tree/v1.1.0-dev) (2021-02-03)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/v1.0.2-dev...v1.1.0-dev)

**Improvements:**

- Develop User Access / Management Strategy [\#91](https://github.com/NASA-PDS/pds-doi-service/issues/91)

**Defects:**

- xlsx file extension for reserve not supported [\#138](https://github.com/NASA-PDS/pds-doi-service/issues/138)
- 'pds-doi-cmd draft' chokes on a legit Product\_Document [\#129](https://github.com/NASA-PDS/pds-doi-service/issues/129)

**Other closed issues:**

- Update API to deactivate 'release' end point, create a 'submit' end-point [\#135](https://github.com/NASA-PDS/pds-doi-service/issues/135)
- Update draft action with new option --lidvid to change from review to draft the status of a DOI [\#134](https://github.com/NASA-PDS/pds-doi-service/issues/134)
- Update release action with --no-review option, make 'with review' default behavior [\#133](https://github.com/NASA-PDS/pds-doi-service/issues/133)
- Update status management in code with Enumeration [\#132](https://github.com/NASA-PDS/pds-doi-service/issues/132)
- Document the security requirements for operational installation of DOI Service [\#124](https://github.com/NASA-PDS/pds-doi-service/issues/124)

## [v1.0.2-dev](https://github.com/NASA-PDS/pds-doi-service/tree/v1.0.2-dev) (2020-12-10)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/v9.8.7...v1.0.2-dev)

**Improvements:**

- API Implementation for DOI Service [\#52](https://github.com/NASA-PDS/pds-doi-service/issues/52)

**Defects:**

- command pds-doi-cmd list returns update date in timestamp instead of iso8601 [\#128](https://github.com/NASA-PDS/pds-doi-service/issues/128)
- update\_date management [\#127](https://github.com/NASA-PDS/pds-doi-service/issues/127)
- get /dois/{lidvid} [\#126](https://github.com/NASA-PDS/pds-doi-service/issues/126)
- the sqllite database should be created at the same location, whereever the command are launched from [\#122](https://github.com/NASA-PDS/pds-doi-service/issues/122)

**Other closed issues:**

- validate the submitted OSTI record against a schema [\#56](https://github.com/NASA-PDS/pds-doi-service/issues/56)

## [v9.8.7](https://github.com/NASA-PDS/pds-doi-service/tree/v9.8.7) (2020-11-24)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/v1.0.1...v9.8.7)

## [v1.0.1](https://github.com/NASA-PDS/pds-doi-service/tree/v1.0.1) (2020-11-24)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/1.0.0...v1.0.1)

**Defects:**

- GET /dois must support empty vid field [\#121](https://github.com/NASA-PDS/pds-doi-service/issues/121)
- configuration files are not well deployed [\#115](https://github.com/NASA-PDS/pds-doi-service/issues/115)
- Be more specific about the supported python version or extend tests [\#92](https://github.com/NASA-PDS/pds-doi-service/issues/92)

**Other closed issues:**

- Extraction of the OSTI XML in /dois?... GET requests [\#116](https://github.com/NASA-PDS/pds-doi-service/issues/116)
- Draft action: read the doi from the pds4 label [\#114](https://github.com/NASA-PDS/pds-doi-service/issues/114)
- Add force argument to the /dois POST function [\#113](https://github.com/NASA-PDS/pds-doi-service/issues/113)
- allow to post PDS4 labels in the payload \(for draft\) [\#107](https://github.com/NASA-PDS/pds-doi-service/issues/107)
- Add exception name in the error messages [\#106](https://github.com/NASA-PDS/pds-doi-service/issues/106)
- Complete get DOIS criterias with the arguments proposed in command line [\#105](https://github.com/NASA-PDS/pds-doi-service/issues/105)
- Add PUT DOI to the API \(for updates\) [\#101](https://github.com/NASA-PDS/pds-doi-service/issues/101)
- Add GET DOI to the API [\#100](https://github.com/NASA-PDS/pds-doi-service/issues/100)
- Be explicit in the install documentation about the test/prod osti server configuration [\#98](https://github.com/NASA-PDS/pds-doi-service/issues/98)
- Develop API specification in SwaggerHub [\#80](https://github.com/NASA-PDS/pds-doi-service/issues/80)
- Add Release DOI function to API [\#79](https://github.com/NASA-PDS/pds-doi-service/issues/79)
- Add POST Reserve xslx/csv DOI function to API [\#78](https://github.com/NASA-PDS/pds-doi-service/issues/78)
- Add POST PDS4 or  OSTI DOI label to API [\#77](https://github.com/NASA-PDS/pds-doi-service/issues/77)
- Mock web UI for DOI management  [\#67](https://github.com/NASA-PDS/pds-doi-service/issues/67)
- Add Status / Query component to API [\#38](https://github.com/NASA-PDS/pds-doi-service/issues/38)

## [1.0.0](https://github.com/NASA-PDS/pds-doi-service/tree/1.0.0) (2020-10-13)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.8-dev...1.0.0)

**Improvements:**

- Write procedure documentation [\#83](https://github.com/NASA-PDS/pds-doi-service/issues/83)
- initialize production deployment with pre-existing dois [\#71](https://github.com/NASA-PDS/pds-doi-service/issues/71)
- Revise DOI Service Requirements [\#65](https://github.com/NASA-PDS/pds-doi-service/issues/65)
- Develop operational documentation and test suite [\#40](https://github.com/NASA-PDS/pds-doi-service/issues/40)

**Defects:**

- node is not provided as contributor in the reserve records [\#72](https://github.com/NASA-PDS/pds-doi-service/issues/72)

**Other closed issues:**

- Update to use pds round-up github action [\#94](https://github.com/NASA-PDS/pds-doi-service/issues/94)
- End to end behave test [\#82](https://github.com/NASA-PDS/pds-doi-service/issues/82)
- add check to ensure landing page is online prior to DOI release [\#70](https://github.com/NASA-PDS/pds-doi-service/issues/70)
- Revise requirements to ensure scope is being met [\#64](https://github.com/NASA-PDS/pds-doi-service/issues/64)
- Develop DOI Service Scope [\#63](https://github.com/NASA-PDS/pds-doi-service/issues/63)
- Add configuration documentation [\#60](https://github.com/NASA-PDS/pds-doi-service/issues/60)
- Perform benchmark tests between original prototype software and new system [\#44](https://github.com/NASA-PDS/pds-doi-service/issues/44)
- Develop simple regression test suite for deployment [\#41](https://github.com/NASA-PDS/pds-doi-service/issues/41)

## [0.0.8-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.8-dev) (2020-09-10)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.7-dev...0.0.8-dev)

## [0.0.7-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.7-dev) (2020-09-10)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.6-dev...0.0.7-dev)

## [0.0.6-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.6-dev) (2020-09-10)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.5-dev...0.0.6-dev)

## [0.0.5-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.5-dev) (2020-09-10)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.4-dev...0.0.5-dev)

## [0.0.4-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.4-dev) (2020-09-10)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.3-dev...0.0.4-dev)

**Defects:**

- Update default DOI metadata according to changes in requirements [\#55](https://github.com/NASA-PDS/pds-doi-service/issues/55)

**Other closed issues:**

- create full\_name when first/last name cannot be parsed [\#58](https://github.com/NASA-PDS/pds-doi-service/issues/58)

## [0.0.3-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.3-dev) (2020-08-18)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.2-dev...0.0.3-dev)

**Other closed issues:**

- Update documentation for operational installation and usage [\#42](https://github.com/NASA-PDS/pds-doi-service/issues/42)
- Develop DOI metadata automated validation component [\#18](https://github.com/NASA-PDS/pds-doi-service/issues/18)

## [0.0.2-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.2-dev) (2020-08-06)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.3...0.0.2-dev)

## [0.0.3](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.3) (2020-07-31)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.2...0.0.3)

## [0.0.2](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.2) (2020-07-31)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/0.0.1-dev...0.0.2)

**Improvements:**

- Re-organize and clean-up code to meet coding standards [\#28](https://github.com/NASA-PDS/pds-doi-service/issues/28)
- Develop DOI Status / Query component [\#27](https://github.com/NASA-PDS/pds-doi-service/issues/27)
- Implement initial DOI database and management [\#26](https://github.com/NASA-PDS/pds-doi-service/issues/26)
- DOI Batch Processing capability [\#25](https://github.com/NASA-PDS/pds-doi-service/issues/25)
- Update Released DOI capability [\#24](https://github.com/NASA-PDS/pds-doi-service/issues/24)
- Release DOI capability [\#22](https://github.com/NASA-PDS/pds-doi-service/issues/22)

**Other closed issues:**

- Implement the command line and parser to release a doi [\#46](https://github.com/NASA-PDS/pds-doi-service/issues/46)
- Develop Pending DOI Handler component for iteratively querying OSTI for DOI status until status change [\#33](https://github.com/NASA-PDS/pds-doi-service/issues/33)
- Develop Status / Query capability for querying database and return JSON [\#32](https://github.com/NASA-PDS/pds-doi-service/issues/32)
- Develop maintain internal database of DOI requests [\#31](https://github.com/NASA-PDS/pds-doi-service/issues/31)
- Develop ability to maintain a transaction log database [\#29](https://github.com/NASA-PDS/pds-doi-service/issues/29)
- Develop Status / Query API and component for OSTI status of a DOI [\#4](https://github.com/NASA-PDS/pds-doi-service/issues/4)
- document requirements and tests [\#3](https://github.com/NASA-PDS/pds-doi-service/issues/3)

## [0.0.1-dev](https://github.com/NASA-PDS/pds-doi-service/tree/0.0.1-dev) (2020-05-08)

[Full Changelog](https://github.com/NASA-PDS/pds-doi-service/compare/cc08fcdce4414bec5d83e1187998538152391642...0.0.1-dev)

**Improvements:**

- Reserve a DOI capability [\#21](https://github.com/NASA-PDS/pds-doi-service/issues/21)
- Develop draft PDS Policy for Assigning DOIs [\#20](https://github.com/NASA-PDS/pds-doi-service/issues/20)
- Design REST API and JSON response [\#19](https://github.com/NASA-PDS/pds-doi-service/issues/19)
- Create / Draft a DOI object capability [\#2](https://github.com/NASA-PDS/pds-doi-service/issues/2)
- Develop initial requirements and design for DOI Service [\#1](https://github.com/NASA-PDS/pds-doi-service/issues/1)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*

# 01 — PoC Goal and Scope

## PoC scenario

This PoC focuses on Bluetooth phone reconnection after a vehicle ignition cycle.

A phone that was previously paired with the vehicle should reconnect automatically after the vehicle starts and the infotainment system becomes ready.

In some test executions, the reconnection may be delayed or may fail completely.

## Goal

The goal is to create a small Neo4j knowledge graph that connects:

* a Bluetooth reconnection feature;
* software requirements;
* software components;
* SiL, HiL, and vehicle tests;
* individual test executions and their results;
* test traces;
* fictional defect tickets.

The graph should support software traceability, test coverage analysis, and basic failure investigation.

All data used in the PoC will be fully synthetic.

## Questions the graph should answer

The knowledge graph should help answer questions such as:

* Which tests verify a requirement?
* Which requirement is connected to a failed test execution?
* Which software component implements the affected requirement?
* Is there a defect ticket related to the failed execution?
* Which requirements have no test coverage?
* Did a similar failure appear in SiL, HiL, or vehicle testing?
* Which test trace was produced by a failed execution?

## Bluetooth reconnection example

### Scenario

A phone was paired with the vehicle before the ignition was switched off.

When the vehicle starts again, the infotainment system should automatically reconnect to that phone.

### Preconditions

* The phone is already paired with the vehicle.
* Bluetooth is enabled on the phone.
* The phone is close to the vehicle.
* No other phone is connected.
* The pairing information is still stored by the infotainment system.

### Trigger

The driver switches the vehicle ignition on, and the infotainment system becomes ready.

### Expected result

The infotainment system should reconnect automatically to the previously paired phone within **10 seconds** after becoming ready.

The value of 10 seconds is a synthetic threshold chosen for this PoC. It is not intended to represent an official company or industry requirement.

After reconnection:

* the phone is displayed as connected;
* Bluetooth audio is available;
* phone-call functionality is available.

### Failure examples

Examples of failures represented in the synthetic data may include:

* the phone does not reconnect;
* reconnection takes longer than 10 seconds;
* the phone connects and immediately disconnects;
* Bluetooth audio becomes available, but phone-call functionality does not;
* reconnection succeeds in SiL but fails in HiL or vehicle testing.

## PoC boundary

The PoC focuses only on reconnecting **one previously paired phone after one ignition cycle**.

The following scenarios are outside the initial boundary:

* multiple paired phones;
* first-time Bluetooth pairing;
* manual reconnection;
* Wi-Fi connectivity;
* Android Auto;
* Apple CarPlay.

## Estimated synthetic dataset

The first version of the PoC will contain approximately:

* 1 feature;
* 5–8 requirements;
* 3–5 software components;
* 8–12 tests;
* 12–20 test executions;
* several test traces;
* 2–4 defect tickets.

These numbers are initial guidelines and may change slightly while building the PoC.

## Success criteria

The PoC is successful when:

1. the main concepts and relationships are clearly defined;
2. the ontology can be understood through a diagram;
3. the synthetic data can be loaded into Neo4j;
4. the relationships can be explored visually;
5. failed test executions can be traced to requirements and software components;
6. related defect tickets can be identified;
7. requirements without test coverage can be found;
8. failures can be compared across SiL, HiL, and vehicle testing;
9. the result can be explained in a short demonstration to the Team Lead.

## Demo example

A vehicle test execution shows that Bluetooth reconnection took **18 seconds**, while the expected maximum duration was **10 seconds**.

The graph should help identify:

* the failed test execution;
* the test that was executed;
* the related requirement;
* the software component that implements the requirement;
* similar failures in other test environments;
* the produced test trace;
* an existing related defect ticket.


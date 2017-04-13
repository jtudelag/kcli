#!/usr/bin/python

# import getpass
# from mock import patch
from flask import Flask, render_template, request, jsonify
from config import Kconfig
import dockerutils
import os

app = Flask(__name__)
try:
    app.config.from_object('settings')
    config = app.config
except ImportError:
    config = {'PORT': os.environ.get('PORT', 9000)}

debug = config['DEBUG'] if 'DEBUG' in config.keys() else True
port = int(config['PORT']) if 'PORT'in config.keys() else 9000


class TABLE(object):
    pass


@app.route("/")
@app.route('/vms')
def vms():
    """
    retrieves all vms
    """
    config = Kconfig()
    k = config.k
    reportdir = config.reportdir
    vms = []
    for vm in k.list():
        name = vm[0]
        if os.path.exists('%s/%s.txt' % (reportdir, name)):
            if os.path.exists('%s/%s.running' % (reportdir, name)):
                vm[6] = 'Running'
            else:
                vm[6] = 'OK'
        vms.append(vm)
    return render_template('vms.html', title='Home', vms=vms)


@app.route('/vmcreate')
def vmcreate():
    """
    create vm
    """
    config = Kconfig()
    profiles = config.list_profiles()
    return render_template('vmcreate.html', title='CreateVm', profiles=profiles)


@app.route('/containercreate')
def containercreate():
    """
    create container
    """
    config = Kconfig()
    profiles = config.list_containerprofiles()
    return render_template('containercreate.html', title='CreateContainer', profiles=profiles)


@app.route('/poolcreate')
def poolcreate():
    """
    create pool
    """
    return render_template('poolcreate.html', title='CreatePool')


@app.route('/networkcreate')
def networkcreate():
    """
    create network
    """
    return render_template('networkcreate.html', title='CreateNetwork')


@app.route('/plancreate')
def plancreate():
    """
    create plan
    """
    return render_template('plancreate.html', title='CreateNetwork')


@app.route("/vmaction", methods=['POST'])
def vmaction():
    """
    start/stop/delete/create vm
    """
    config = Kconfig()
    k = config.k
    if 'name' in request.form:
        name = request.form['name']
        action = request.form['action']
        if action == 'start':
            result = k.start(name)
        elif action == 'stop':
            result = k.stop(name)
        elif action == 'delete':
            result = k.delete(name)
        elif action == 'create' and 'profile' in request.form:
            profile = request.form['profile']
            result = config.create_vm(name, profile)
        else:
            result = "Nothing to do"
        print(result)
        response = jsonify(result)
        print(response)
        response.status_code = 200
        return response
    else:
        failure = {'result': 'failure', 'reason': "Invalid Data"}
        response = jsonify(failure)
        response.status_code = 400
        return jsonify(failure)


@app.route("/vmsnapshot", methods=['POST'])
def vmsnapshot():
    """
    snapshot vm
    """
    config = Kconfig()
    k = config.k
    if 'name' in request.form:
        snapshot = request.form['snapshot']
        name = request.form['name']
        result = k.snapshot(snapshot, name, revert=False, delete=False)
        print(result)
        response = jsonify(result)
        print(response)
        response.status_code = 200
        return response
    else:
        failure = {'result': 'failure', 'reason': "Invalid Data"}
        response = jsonify(failure)
        response.status_code = 400
        return jsonify(failure)


@app.route("/planaction", methods=['POST'])
def planaction():
    """
    start/stop/delete plan
    """
    config = Kconfig()
    if 'name' in request.form:
        plan = request.form['name']
        action = request.form['action']
        if action == 'start':
            result = config.plan(plan, start=True)
        elif action == 'stop':
            result = config.plan(plan, stop=True)
        elif action == 'delete':
            result = config.plan(plan, delete=True)
        # elif action == 'create' and 'profile' in request.form:
        #    profile = request.form['profile']
        #     result = config.create_plan(name, profile)
        else:
            result = "Nothing to do"
        print(result)
        response = jsonify(result)
        print(response)
        response.status_code = 200
        return response
    else:
        failure = {'result': 'failure', 'reason': "Invalid Data"}
        response = jsonify(failure)
        response.status_code = 400


@app.route("/report", methods=['POST'])
def report():
    """
    updatestatus
    """
    config = Kconfig()
    k = config.k
    reportdir = config.reportdir
    if 'name' in request.form and 'report' in request.form and 'status' in request.form:
        name = request.form['name']
        status = request.form['status']
        report = request.form['report']
    if not k.exists(name):
        return "KO"
    k.update_metadata(name, 'report', status)
    if not os.path.exists(reportdir):
        os.mkdir(reportdir)
    with open("%s/%s.txt" % (reportdir, name), 'w') as f:
        f.write(report)
    print("Name: %s Status: %s" % (name, status))
    if status == 'Running' and not os.path.exists("%s/%s.running" % (reportdir, name)):
        open("%s/%s.running" % (reportdir, name), 'a').close()
    if status == 'OK' and os.path.exists("%s/%s.running" % (reportdir, name)):
        os.remove("%s/%s.running" % (reportdir, name))
    return 'OK'


@app.route('/containers')
def containers():
    """
    retrieves all containers
    """
    config = Kconfig()
    k = config.k
    containers = dockerutils.list_containers(k)
    return render_template('containers.html', title='Containers', containers=containers)


@app.route('/networks')
def networks():
    """
    retrieves all networks
    """
    config = Kconfig()
    k = config.k
    networks = k.list_networks()
    return render_template('networks.html', title='Networks', networks=networks)


@app.route('/pools')
def pools():
    """
    retrieves all pools
    """
    config = Kconfig()
    k = config.k
    pools = []
    for pool in k.list_pools():
        poolpath = k.get_pool_path(pool)
        pools.append([pool, poolpath])
    return render_template('pools.html', title='Pools', pools=pools)


@app.route('/plans')
def plans():
    """
    retrieves all plans
    """
    config = Kconfig()
    return render_template('plans.html', title='Plans', plans=config.list_plans())


@app.route("/containeraction", methods=['POST'])
def containeraction():
    """
    start/stop/delete container
    """
    config = Kconfig()
    k = config.k
    if 'name' in request.form:
        name = request.form['name']
        action = request.form['action']
        if action == 'start':
            result = dockerutils.start_container(k, name)
        elif action == 'stop':
            result = dockerutils.stop_container(k, name)
        elif action == 'delete':
            result = dockerutils.delete_container(k, name)
        else:
            result = "Nothing to do"
        print(result)
        response = jsonify(result)
        response.status_code = 200
        return response
    else:
        failure = {'result': 'failure', 'reason': "Invalid Data"}
        response.status_code = 400
        return jsonify(failure)


@app.route('/vmprofiles')
def vmprofiles():
    """
    retrieves vm profiles
    """
    config = Kconfig()
    profiles = config.list_profiles()
    return render_template('vmprofiles.html', title='VMProfiles', profiles=profiles)


@app.route('/containerprofiles')
def containerprofiles():
    """
    retrieves vm profiles
    """
    config = Kconfig()
    profiles = config.list_containerprofiles()
    return render_template('containerprofiles.html', title='ContainerProfiles', profiles=profiles)


def run():
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    # global k
    # config = Kconfig()
    # k = config.k
    # with patch.object(getpass, "getuser", return_value='default'):
    # app.run(host='0.0.0.0', port=port, debug=debug)
    run()
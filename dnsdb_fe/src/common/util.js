import _ from 'lodash'

function urlParam (name) {
  var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href)
  if (results === null) {
    return null
  }
  return results[1] || 0
}

function deepCopy (source) {
  var result = {}
  for (var key in source) {
    result[key] = typeof source[key] === 'object' ? deepCopy(source[key]) : source[key]
  }
  return result
}

var confirm = function (self, title, ok, params) {
  self.$confirm(title, '确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => { ok(params) })
    .catch(() => {})
}

var notify = function (self, title, message, type) {
  if (!type) {
    type = 'success'
  }
  self.$notify({
    title: title,
    message: message,
    type: type,
    duration: 1500
  })
}

var get = function (self, params) {
  let mergedParams = _.merge({
    url: '',
    data: null,
    succ: (data) => {
      self.$notify.success({
        title: '成功',
        message: 'API调用成功',
        duration: 1500
      })
    },
    fail: (res) => {
      if (res.errcode === 401) {
        self.$router.push('/login')
        return
      }
      self.$notify.error({
        title: '获取数据失败',
        message: res.message,
        duration: 1500
      })
    }
  }, params)
  self.$http.get(mergedParams.url, {params: mergedParams.data})
    .then((res) => {
      var errcode = res.data.errcode
      if (errcode !== 0) {
        mergedParams.fail(res.data)
      } else {
        mergedParams.succ(res.data)
      }
    })
    .catch((err) => {
      if (err.status === 401) {
        self.$router.push('/login')
        return
      }
      self.$notify.error({
        title: '异常',
        message: '状态码:' + err.status,
        duration: 1500
      })
    })
}

var post = function (self, params) {
  let mergedParams = _.merge({
    url: '',
    data: null,
    succStr: 'API调用成功',
    succ: (data) => {
      self.$notify.success({
        title: '成功',
        message: mergedParams.succStr,
        duration: 1500
      })
    },
    fail: (data) => {
      if (data.errcode === 401) {
        self.$router.push('/login')
        return
      }
      self.$confirm(data.message + '，请检查后重试', '失败', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
        .then(() => {})
        .catch(() => {})
    }
  }, params)
  self.$http.post(mergedParams.url, mergedParams.data)
    .then((res) => {
      var errcode = res.data.errcode
      if (errcode !== 0) {
        mergedParams.fail(res.data)
      } else {
        mergedParams.succ(res.data)
      }
    })
    .catch((err) => {
      console.log(err)
      if (err.status === 401) {
        self.$router.push('/login')
        return
      }
      self.$notify.error({
        title: '异常',
        message: '状态码:' + err.status,
        duration: 1500
      })
    })
}

var strTrim = function (self, prop) {
  console.log(prop)
  self[prop] = self[prop].trim()
}

var arrayToOptions = function (array) {
  var options = []
  for (let i in array) {
    var item = {}
    item.label = array[i]
    item.value = array[i]
    options.push(item)
  }
  return options
}

var objToOptions = function (obj) {
  let options = []
  for (let i in obj) {
    var item = {}
    item.label = obj[i]
    item.value = i
    options.push(item)
  }
  return options
}

var objArrayToOptions = function (array, label, value) {
  var options = []
  for (let i in array) {
    var item = {}
    item.label = array[i][label]
    item.value = array[i][value]
    options.push(item)
  }
  return options
}

// check whether every char of the str is a Hex char(0~9,a~f,A~F)
var isHex = function (str) {
  var reg = /^[0-9A-Fa-f]{1,4}$/
  return reg.test(str)
}

var isValidIpv6 = function (ip) {
  ip = ip.trim()
  var idx = ip.indexOf('::')
  // there is no "::" in the ip address
  if (idx < 0) {
    let items = ip.split(':')
    if (items.length !== 8) {
      return false
    }
    for (let tag of items) {
      if (!isHex(tag)) {
        return false
      }
    }
    return true
  } else {
    // The "::" can only appear once in an address
    if (idx !== ip.lastIndexOf('::')) {
      return false
    }
    if (ip.split(':').length > 8) {
      return false
    }
    var items = ip.split('::')
    for (let tags of items) {
      if (!tags) {
        continue
      }
      for (let tag of tags.split(':')) {
        if (!isHex(tag)) {
          return false
        }
      }
    }
    return true
  }
}

var isValidIpv4 = function (ip) {
  ip = ip.trim()
  var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}$/
  return reg.test(ip)
}

var isValidIP = function (ip) {
  if (ip.indexOf(':') > 0) {
    return isValidIpv6(ip)
  } else {
    return isValidIpv4
  }
}

var isValidDomain = function (domain) {
  let reg = /^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+$/
  return reg.test(domain)
}

export default {
  confirm,
  notify,
  get,
  post,
  urlParam,
  deepCopy,
  strTrim,
  arrayToOptions,
  objArrayToOptions,
  objToOptions,
  isValidIP,
  isValidIpv6,
  isValidIpv4,
  isValidDomain
}

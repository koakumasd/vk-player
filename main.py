#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk, gobject
import pygst
pygst.require("0.10")
import gst
from vkappauth import VKAppAuth
import urllib
import urllib2
import getpass
from urllib import urlencode
import sys
import lxml
import lxml.html
import threading
import datetime
import time
import gobject
from random import randint
import os


class Player(gtk.Window):
	
	def seeker_button_release_event(self, widget, event):
		# print "seeker_button_release_event"
		value =  widget.get_value()
		if self.is_playing == True:
			duration = self.player.query_duration(self.time_format, None)[0]
			time = value * (duration / 100)
			self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, time)
	def vol_change(self,widget,event):
		value =  widget.get_value()
		# print value
		self.player.set_property("volume", value)
	def mode(self):
		if self.repeat_button.get_active()==1: 
			return 1
		elif self.shuffle_button.get_active()==1: 
			return 2
		else: 
			return 3


	def what_play(self,i):		
		n=self.mode()
		self.pipeline.set_state(gst.STATE_NULL)
		if i==3:
			if n==1:
				# print "repeat"
				return self.play()
			elif n==3:
				# print "next track"
				self.value=int(self.value)+1
				return self.play()
			elif n==2:
				print self.count
				self.value=randint(0,self.count-1)
				return self.play()
		
		elif i==4:
			# print "prev track"
			if self.value==0:
				pass
			elif n==2 or self.value>1:
				self.value=int(self.value)-1
			return self.play()
	# def on_treeview_button_press_event(self, treeview, event):
	# 	if event.button == 3:
	# 		x = int(event.x)
	# 		y = int(event.y)
	# 		time = event.time
	# 		pthinfo = treeview.get_path_at_pos(x, y)
	# 		if pthinfo is not None:
	# 			path, col, cellx, celly = pthinfo
	# 			treeview.grab_focus()
	# 			treeview.set_cursor( path, col, 0)
	# 			self.popup.popup( None, None, None, event.button, time)
	# 		return True

	def check_state(self):
		# print self.is_playing
		if self.is_playing==0:
			self.play_button.set_label("Play")
			self.play_button.connect("clicked",self.play)
			# self.play
			# print "play"
		else:
			self.play_button.set_label("Pause")
			self.play_button.connect("clicked",self.pause)
	def callback(self):
		self.pipeline.get_state()
		self.check_state()
		state=str(self.pipeline.get_state()[1])
		format = self.time_format
		duration = self.pipeline.query_duration(format)[0]
		duration_time=datetime.timedelta(seconds=duration/1000000000)
		now = self.pipeline.query_position(gst.FORMAT_TIME, None)[0]
		now_time=datetime.timedelta(seconds=now/1000000000)
		state=str(self.pipeline.get_state()[1])
		percent = (float(now)/float(duration))*100.0
		adjustment = gtk.Adjustment(percent, 0.00, 100.0, 0.1, 1.0, 1.0)
		self.time_scale.set_adjustment(adjustment)
		timer=str(now_time) +"/"+str(duration_time)
		self.label.set_text(timer)
		d=duration/1000000000-0.5
		n=now/1000000000
		now=+1 +(10 * 1000000000)
		
		if n>=d:
			self.what_play(3)
		return True

	def onSelectionChanged(self,w):
		self.pipeline.set_state(gst.STATE_NULL)
		(self.model, self.pathlist) = self.tree_selection.get_selected_rows()

		for path in self.pathlist :
			tree_iter = self.model.get_iter(path)
			self.value = self.model.get_value(tree_iter,0)
		self.play()

	def on_message(self, bus, message):
		t = message.type
		if t == Gst.Message.EOS:
			self.pipeline.set_state(gst.STATE_NULL)
			self.playing = False
		elif t == Gst.Message.ERROR:
			self.pipeline.set_state(gst.STATE_NULL)
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.playing = False
	def on_sync_message(self, bus, message):
	   if message.structure is None:
		   return
	   message_name = message.structure.get_name()
	   if message_name == 'prepare-xwindow-id':
		   imagesink = message.src
		   imagesink.set_property('force-aspect-ratio', True)
		   imagesink.set_xwindow_id(self.movie_window.GetHandle())
	def play(self, *args, **kwargs):
		# self.pipeline.set_state(gst.STATE_NULL)
		self.is_playing=1
		info=str(self.artistArr[int(self.value)]) + "-" + str(self.titleArr[int(self.value)])
		self.now_play=self.value
		self.label2.set_text(info)
		# self.pipeline.set_state(gst.STATE_NULL)
		music_stream_uri =self.urlArr[int(self.value)]
		# print music_stream_uri
		self.player.set_property('uri', music_stream_uri)
		self.pipeline.set_state(gst.STATE_PLAYING)
	def pause(self, *args, **kwargs):
		self.is_playing=0
		self.pipeline.set_state(gst.STATE_PAUSED)
		self.check_state()
		return 
		
	def clear_list(self):
		del self.artistArr[:]
		del self.urlArr[:]
		del self.titleArr[:]
		del self.durationArr[:]
		self.liststore.clear()

	def get(self):
		import vkontakte
		vkaa = VKAppAuth()
		self.combo.get_model().clear
		app_id = 4443059
		scope = ['audio', 'online']
		email="380507324544"
		password= "dominiccFR5698560"
		access_data = vkaa.auth(email, password, app_id, scope)
		self.vk = vkontakte.API(token=access_data['access_token'])
		# print self.friend_name.keys()
		self.combo.get_model().clear()
		i=0
		audio = self.vk.get('audio.get')
		for d in audio:
			self.urlArr.append(d.get('url'))
			self.titleArr.append(d.get('title'))
			self.artistArr.append(d.get('artist'))
			self.durationArr.append(d.get('duration'))
			self.liststore.append([int(i),self.artistArr[i],self.titleArr[i],datetime.timedelta(seconds=self.durationArr[i])])

			i=i+1
		self.count=i
		# print self.friend_name.keys()
		friend = self.vk.get('friends.get',name_case="ins",fields="name")
		n=0
		for x in friend:
			self.friend_name.update({x.get('first_name')+" "+x.get('last_name'): x.get('user_id')})
			# print n
			self.combo.append_text(self.friend_name.keys()[n])
			n=n+1
		# self.friend_name['name']
		# print self.friend_name.keys()
	def search(self,s):
		self.clear_list()
		i=0
		if self.search_entry.get_text()=="":
			self.get()
		elif self.search_entry.get_text().isdigit():
			audio = self.vk.get('audio.get',owner_id=int(self.search_entry.get_text()))
			for x in range(1,len(audio)):
				self.urlArr.append(audio[x]['url'])
				self.titleArr.append(audio[x]['title'])
				self.artistArr.append(audio[x]['artist'])
				self.durationArr.append(audio[x]['duration'])
				self.idArr.append(audio[x]['aid'])
				self.ownerArr.append(audio[x]['owner_id'])
				self.liststore.append([int(i),self.artistArr[i],self.titleArr[i],datetime.timedelta(seconds=self.durationArr[i])])
				i=i+1
			self.count=i
		elif self.search_entry.get_text().isdigit()==0:
			audio=self.vk.get('audio.search', q=self.search_entry.get_text(),count=400,auto_complete=1)
			# print audio
			for x in range(1,len(audio)):
				self.urlArr.append(audio[x]['url'])
				self.titleArr.append(audio[x]['title'])
				self.artistArr.append(audio[x]['artist'])
				self.durationArr.append(audio[x]['duration'])
				self.idArr.append(audio[x]['aid'])
				self.ownerArr.append(audio[x]['owner_id'])
				self.liststore.append([int(i),self.artistArr[i],self.titleArr[i],datetime.timedelta(seconds=self.durationArr[i])])
				self.tree_selection.connect("button-press-event", self.onSelectionChanged)
				i=i+1
			self.count=i
	def hello(self,w):
		f_name=""
		f_name=self.combo.get_active_text()
		# print self.friend_name[f_name]
		uid=self.friend_name[f_name]
		# uid=167213745
		audio = self.vk.get('audio.get',owner_id=uid)
		i=0
		self.clear_list()
		for x in range(1,len(audio)):
			self.urlArr.append(audio[x]['url'])
			self.titleArr.append(audio[x]['title'])
			self.artistArr.append(audio[x]['artist'])
			self.durationArr.append(audio[x]['duration'])
			self.idArr.append(audio[x]['aid'])
			self.ownerArr.append(audio[x]['owner_id'])
			self.liststore.append([int(i),self.artistArr[i],self.titleArr[i],datetime.timedelta(seconds=self.durationArr[i])])
			i=i+1
		self.count=i
	def __init__(self):
		self.is_playing=0
		self.pathlist=""
		self.now_play=0
		self.friend=[]
		self.friend_name={}
		self.time_format=gst.Format(gst.FORMAT_TIME)
		self.titleArr = []
		self.artistArr= []
		self.durationArr =[]
		self.urlArr = []
		self.idArr= []
		self.ownerArr = []
		self.count = 0
		self.value=0
		self.pipeline = gst.Pipeline("mypipeline")
		self.player = gst.element_factory_make("playbin", "player")
		self.pipeline.add(self.player)
		self.bus = self.player.get_bus()
		self.bus.add_signal_watch()
		self.bus.enable_sync_message_emission()
		self.bus.connect('message', self.on_message)
		self.bus.connect('sync-message::element', self.on_sync_message)
		self.combo=gtk.combo_box_new_text()
		self.combo.connect("changed",self.hello)
		# self.combo.add()
		# self.player.link(self.sink)
		self.liststore = gtk.ListStore(int, str, str,str)
		self.label = gtk.Label('0:00:00/0:00:00')
		self.label2=gtk.Label("Hello Maffaka")
		self.shuffle_button= gtk.CheckButton(label="shuffle")
		# self.shuffle_button.connect("toggled", self.callback, "toggle button 1")
		self.repeat_button= gtk.CheckButton(label="repeat")
		# self.repeat_button.connect("toggled", self.callback, "toggle button 1")
		self.app_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.app_window.set_border_width(10)
		self.time_adj = gtk.Adjustment(0.0, 0.00, 100.0, 0.1, 1.0, 1.0)
		self.volume_adj = gtk.Adjustment(0.0, 0.00, 3.0, 0.01, 1.0, 1.0)
		self.time_scale=gtk.HScale()
		self.volume_scale=gtk.HScale()
		self.volume_scale.set_adjustment(self.volume_adj)
		self.volume_scale.set_draw_value(False)
		self.volume_scale.set_value(1)
		self.volume_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
		self.volume_scale.connect("button-release-event", self.vol_change)
		self.time_scale.set_draw_value(False)
		self.time_scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
		self.time_scale.connect("button-release-event", self.seeker_button_release_event)
		self.search_button=gtk.Button("Search")
		self.search_button.connect("clicked",self.search)
		self.search_button.set_size_request(80, 40)
		self.search_entry=gtk.Entry()
		self.play_button=gtk.Button("Play")
		self.prev_button=gtk.Button("Prev")
		self.next_button=gtk.Button("Next")
		self.next_button.connect("clicked",lambda w:self.what_play(3))
		self.prev_button.connect("clicked",lambda w:self.what_play(4))
		self.app_window.set_title("Vk player")
		self.app_window.connect("delete_event", lambda w,e: gtk.main_quit())
		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.set_border_width(10)
		self.app_window.set_default_size(675,2000)
		self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		self.scrolled_window.show()    
		self.treeview = gtk.TreeView(model=self.liststore)

		self.treeview.set_model(self.liststore)
		self.tree_selection = self.treeview.get_selection()
		self.tree_selection.set_mode(gtk.SELECTION_SINGLE)
		self.tree_selection.connect("changed",self.onSelectionChanged)
		self.renderer_text1 = gtk.CellRendererText()

		self.column_text1 = gtk.TreeViewColumn("ID", self.renderer_text1, text=0)
		self.column_text1.set_max_width(250)
		self.column_text1.set_resizable(1)
		self.treeview.append_column(self.column_text1)
		self.column_text1.set_sort_column_id(0)
		
		self.renderer_text = gtk.CellRendererText()
		self.column_text = gtk.TreeViewColumn("ARTIST", self.renderer_text, text=1)
		self.column_text.set_max_width(250)
		self.column_text.set_resizable(1)
		self.treeview.append_column(self.column_text)
		self.column_text.set_sort_column_id(1)

		self.renderer_text2 = gtk.CellRendererText()
		self.column_text2 = gtk.TreeViewColumn("TITLE", self.renderer_text2, text=2)
		self.column_text2.set_max_width(250)
		self.column_text2.set_resizable(1)
		self.treeview.append_column(self.column_text2)
		self.column_text2.set_sort_column_id(2)

		self.renderer_text3 = gtk.CellRendererText()
		self.column_text3 = gtk.TreeViewColumn("DURATION", self.renderer_text3, text=3)
		self.column_text3.set_max_width(250)
		self.column_text3.set_resizable(1)
		self.treeview.append_column(self.column_text3)
		self.column_text3.set_sort_column_id(3)
		self.panel1=gtk.HButtonBox()
		self.panel1.add(self.prev_button)
		self.panel1.add(self.play_button)
		self.panel1.add(self.next_button)
		self.panel1.add(self.repeat_button)
		self.panel1.add(self.shuffle_button)
		self.panel1.add(self.volume_scale)
		self.scrolled_window.add(self.treeview)
		self.vbox_app = gtk.VBox(False, 0)
		self.treeview.set_enable_search(1)
		self.treeview.set_search_column(1)
		self.treeview.set_search_column(2)
		# self.treeview.set_search_column(self.column_text2)
		self.vbox_app.pack_start(self.label2,False,False,1)
		self.vbox_app.pack_start(self.label,False,False,1)
		self.vbox_app.pack_start(self.time_scale,False,False,1)
		self.vbox_app.pack_start(self.panel1,False,False,1)
		self.vbox_app.pack_start(self.search_entry,False,False,1)
		self.vbox_app.pack_start(self.search_button,False,False,1)
		self.vbox_app.pack_start(self.combo,False,False,1)
		self.app_window.add(self.vbox_app)
		self.vbox_app.show()

		self.hbox_close = gtk.HBox(False, 1)
		
		self.hbox_close.pack_start(self.treeview,False,False,1)
		self.hbox_close.pack_start(self.scrolled_window, True, True, 0)
		self.hbox_close.show()
		self.vbox_app.add(self.hbox_close)
		gobject.timeout_add(400, self.callback)
		self.get()
		self.play()
		self.get()
		
		self.app_window.show_all()

		
		return 
def main():
	gtk.main()

if __name__ == "__main__":
	player=Player()
	main()

